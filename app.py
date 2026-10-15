
from flask import Flask, render_template, request, redirect, url_for, flash
from db import get_connection

app = Flask(__name__)
app.secret_key = "aero-maintain-dev-key-change-this"

app = Flask(__name__)
app.secret_key = "aero-maintain-dev-key-change-this"


def get_dashboard_stats(cursor):
    stats = {}

    queries = {
        "aircraft": "SELECT COUNT(*) FROM AIRCRAFT_LOG",
        "hangars": "SELECT COUNT(*) FROM HANGAR_FACILITY",
        "technicians": "SELECT COUNT(*) FROM MAINTENANCE_TECHNICIAN",
        "alerts": """
            SELECT COUNT(*) FROM MAINTENANCE_ALERT
            WHERE UPPER(STATUS) NOT IN ('CLOSED', 'RESOLVED')
        """,
        "scheduled": """
            SELECT COUNT(*) FROM MAINTENANCE_SCHEDULE
            WHERE UPPER(STATUS) = 'SCHEDULED'
        """,
        "in_progress": """
            SELECT COUNT(*) FROM MAINTENANCE_SCHEDULE
            WHERE UPPER(STATUS) = 'IN PROGRESS'
        """,
        "completed": """
            SELECT COUNT(*) FROM MAINTENANCE_SCHEDULE
            WHERE UPPER(STATUS) = 'COMPLETED'
        """,
        "low_stock": """
            SELECT COUNT(*) FROM SPARE_PART
            WHERE QUANTITY_IN_STOCK <= 5
        """,
        "critical_alerts": """
            SELECT COUNT(*) FROM MAINTENANCE_ALERT
            WHERE UPPER(SEVERITY) = 'CRITICAL'
              AND UPPER(STATUS) NOT IN ('CLOSED', 'RESOLVED')
        """
    }

    for key, sql in queries.items():
        cursor.execute(sql)
        stats[key] = cursor.fetchone()[0]

    return stats


@app.route("/")
def dashboard():
    connection = None
    stats = {
        "aircraft": 0,
        "hangars": 0,
        "technicians": 0,
        "alerts": 0,
        "scheduled": 0,
        "in_progress": 0,
        "completed": 0,
        "low_stock": 0,
        "critical_alerts": 0
    }
    recent = []
    error = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        stats = get_dashboard_stats(cursor)

        cursor.execute("""
            SELECT s.TAIL_NUMBER,
                   s.MAINTENANCE_TYPE,
                   s.SCHEDULED_DATE,
                   s.STATUS
            FROM MAINTENANCE_SCHEDULE s
            ORDER BY s.SCHEDULED_DATE DESC NULLS LAST
            FETCH FIRST 10 ROWS ONLY
        """)

        recent = [
            (
                row[0],
                row[1],
                row[2].strftime("%d %b %Y") if row[2] else "Not set",
                row[3]
            )
            for row in cursor.fetchall()
        ]

        cursor.close()

    except Exception as e:
        error = str(e)

    finally:
        if connection:
            connection.close()

    return render_template(
        "dashboard.html",
        stats=stats,
        recent=recent,
        error=error
    )



@app.route("/debug-db")
def debug_db():
    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                SYS_CONTEXT('USERENV', 'SESSION_USER'),
                SYS_CONTEXT('USERENV', 'SERVICE_NAME')
            FROM DUAL
        """)
        user, service = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*)
            FROM USER_TABLES
            WHERE TABLE_NAME = 'AIRCRAFT_LOG'
        """)
        table_count = cursor.fetchone()[0]

        cursor.close()

        return {
            "connected_user": user,
            "service_name": service,
            "aircraft_log_in_current_schema": table_count
        }

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if connection:
            connection.close()


@app.route("/aircraft", methods=["GET", "POST"])
def aircraft_management():
    connection = None
    aircraft = []
    facilities = []
    error = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Process the registration form
        if request.method == "POST":
            tail_number = request.form.get("tail_number", "").strip().upper()
            model = request.form.get("aircraft_model", "").strip()
            flight_hours_text = request.form.get("flight_hours", "").strip()
            maintenance_type = request.form.get("maintenance_type", "").strip()
            facility_id_text = request.form.get("facility_id", "").strip()

            if not all([
                tail_number, model, flight_hours_text,
                maintenance_type, facility_id_text
            ]):
                flash("Please fill in every field.", "error")

            else:
                try:
                    flight_hours = float(flight_hours_text)
                    facility_id = int(facility_id_text)

                    if flight_hours < 0:
                        raise ValueError("Flight hours cannot be negative.")

                    # Check that the tail number is not already registered
                    cursor.execute(
                        "SELECT COUNT(*) FROM AIRCRAFT_LOG WHERE TAIL_NUMBER = :tail",
                        {"tail": tail_number}
                    )

                    if cursor.fetchone()[0] > 0:
                        flash("That tail number is already registered.", "error")
                    else:
                        cursor.execute("""
                            INSERT INTO AIRCRAFT_LOG
                                (TAIL_NUMBER, AIRCRAFT_MODEL, FLIGHT_HOURS,
                                 MAINTENANCE_TYPE, FACILITY_ID)
                            VALUES
                                (:tail, :model, :hours, :maintenance, :facility)
                        """, {
                            "tail": tail_number,
                            "model": model,
                            "hours": flight_hours,
                            "maintenance": maintenance_type,
                            "facility": facility_id
                        })

                        connection.commit()
                        flash("Aircraft registered successfully!", "success")
                        return redirect(url_for("aircraft_management"))

                except ValueError as validation_error:
                    flash(str(validation_error) or "Enter valid numeric values.", "error")

                except Exception as insert_error:
                    connection.rollback()
                    flash(
                        "Could not register aircraft. Check the values and "
                        "make sure the selected facility exists. "
                        + str(insert_error),
                        "error"
                    )

        # Load existing hangar facilities for the dropdown
        cursor.execute("""
            SELECT FACILITY_ID, FACILITY_NAME
            FROM HANGAR_FACILITY
            ORDER BY FACILITY_ID
        """)
        facilities = cursor.fetchall()

        # Load the aircraft records
        cursor.execute("""
            SELECT TAIL_NUMBER, AIRCRAFT_MODEL, FLIGHT_HOURS,
                   MAINTENANCE_TYPE, FACILITY_ID
            FROM AIRCRAFT_LOG
            ORDER BY TAIL_NUMBER
        """)
        aircraft = cursor.fetchall()

        cursor.close()

    except Exception as e:
        error = str(e)

    finally:
        if connection:
            connection.close()

    return render_template(
        "aircraft.html",
        aircraft=aircraft,
        facilities=facilities,
        error=error
    )


@app.route("/aircraft/edit/<tail_number>", methods=["GET", "POST"])
def edit_aircraft(tail_number):
    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        if request.method == "POST":
            model = request.form.get("aircraft_model", "").strip()
            hours_text = request.form.get("flight_hours", "").strip()
            maintenance = request.form.get("maintenance_type", "").strip()
            facility_text = request.form.get("facility_id", "").strip()

            if not all([model, hours_text, maintenance, facility_text]):
                flash("Please fill in every field.", "error")
            else:
                try:
                    hours = float(hours_text)
                    facility_id = int(facility_text)

                    if hours < 0:
                        raise ValueError("Flight hours cannot be negative.")

                    cursor.execute("""
                        UPDATE AIRCRAFT_LOG
                        SET AIRCRAFT_MODEL = :model,
                            FLIGHT_HOURS = :hours,
                            MAINTENANCE_TYPE = :maintenance,
                            FACILITY_ID = :facility
                        WHERE TAIL_NUMBER = :tail
                    """, {
                        "model": model,
                        "hours": hours,
                        "maintenance": maintenance,
                        "facility": facility_id,
                        "tail": tail_number
                    })

                    if cursor.rowcount == 0:
                        connection.rollback()
                        flash("Aircraft not found.", "error")
                    else:
                        connection.commit()
                        flash("Aircraft updated successfully!", "success")
                        return redirect(url_for("aircraft_management"))

                except ValueError as validation_error:
                    flash(str(validation_error) or "Enter valid numeric values.", "error")

                except Exception as update_error:
                    connection.rollback()
                    flash("Could not update aircraft: " + str(update_error), "error")

        cursor.execute("""
            SELECT TAIL_NUMBER, AIRCRAFT_MODEL, FLIGHT_HOURS,
                   MAINTENANCE_TYPE, FACILITY_ID
            FROM AIRCRAFT_LOG
            WHERE TAIL_NUMBER = :tail
        """, {"tail": tail_number})
        aircraft = cursor.fetchone()

        if aircraft is None:
            cursor.close()
            flash("Aircraft not found.", "error")
            return redirect(url_for("aircraft_management"))

        cursor.execute("""
            SELECT FACILITY_ID, FACILITY_NAME
            FROM HANGAR_FACILITY
            ORDER BY FACILITY_ID
        """)
        facilities = cursor.fetchall()
        cursor.close()

        return render_template(
            "aircraft_edit.html",
            aircraft=aircraft,
            facilities=facilities
        )

    except Exception as e:
        flash("Database error: " + str(e), "error")
        return redirect(url_for("aircraft_management"))

    finally:
        if connection:
            connection.close()


@app.route("/aircraft/delete/<tail_number>", methods=["POST"])
def delete_aircraft(tail_number):
    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM AIRCRAFT_LOG
            WHERE TAIL_NUMBER = :tail
        """, {"tail": tail_number})

        if cursor.rowcount == 0:
            connection.rollback()
            flash("Aircraft not found.", "error")
        else:
            connection.commit()
            flash("Aircraft deleted successfully.", "success")

        cursor.close()

    except Exception as e:
        if connection:
            connection.rollback()
        flash(
            "Could not delete aircraft. Related maintenance schedules "
            "or alerts may reference it. Details: " + str(e),
            "error"
        )

    finally:
        if connection:
            connection.close()

    return redirect(url_for("aircraft_management"))


@app.route("/schedules")
def schedules():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT SCHEDULE_ID, TAIL_NUMBER, SCHEDULED_DATE,
                   MAINTENANCE_TYPE, STATUS, TECHNICIAN_ID
            FROM MAINTENANCE_SCHEDULE
            ORDER BY SCHEDULED_DATE
        """)
        schedule_rows = cursor.fetchall()

        cursor.execute("""
            SELECT SCHEDULE_ID, TAIL_NUMBER, SCHEDULED_DATE,
                   MAINTENANCE_TYPE, STATUS, TECHNICIAN_ID
            FROM MAINTENANCE_SCHEDULE
            ORDER BY SCHEDULE_ID
        """)
        schedule_ids = {row[0] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT TAIL_NUMBER FROM AIRCRAFT_LOG ORDER BY TAIL_NUMBER
        """)
        aircraft_list = cursor.fetchall()

        cursor.execute("""
            SELECT TECHNICIAN_ID, TECHNICIAN_NAME, SPECIALIZATION
            FROM MAINTENANCE_TECHNICIAN
            ORDER BY TECHNICIAN_ID
        """)
        technicians = cursor.fetchall()

        technician_names = {
            row[0]: row[1] for row in technicians
        }

        schedules_with_names = [
            (
                row[0], row[1], row[2], row[3], row[4],
                technician_names.get(row[5], str(row[5]))
            )
            for row in schedule_rows
        ]

        return render_template(
            "schedules.html",
            schedules=schedules_with_names,
            aircraft_list=aircraft_list,
            technicians=technicians
        )
    finally:
        cursor.close()
        connection.close()


@app.route("/schedules/add", methods=["POST"])
def add_schedule():
    tail_number = request.form["tail_number"]
    scheduled_date = request.form["scheduled_date"]
    maintenance_type = request.form["maintenance_type"]
    technician_id = int(request.form["technician_id"])

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT NVL(MAX(SCHEDULE_ID), 700) + 1
            FROM MAINTENANCE_SCHEDULE
        """)
        schedule_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO MAINTENANCE_SCHEDULE
                (SCHEDULE_ID, TAIL_NUMBER, SCHEDULED_DATE,
                 MAINTENANCE_TYPE, STATUS, TECHNICIAN_ID)
            VALUES
                (:schedule_id, :tail_number,
                 TO_DATE(:scheduled_date, 'YYYY-MM-DD'),
                 :maintenance_type, 'Scheduled', :technician_id)
        """, {
            "schedule_id": schedule_id,
            "tail_number": tail_number,
            "scheduled_date": scheduled_date,
            "maintenance_type": maintenance_type,
            "technician_id": technician_id
        })

        connection.commit()
        flash("Maintenance schedule added successfully!", "success")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("schedules"))


@app.route("/schedules/<int:schedule_id>/status", methods=["POST"])
def update_schedule_status(schedule_id):
    status = request.form["status"]

    if status not in ("Scheduled", "In Progress", "Completed"):
        flash("Invalid maintenance status.", "error")
        return redirect(url_for("schedules"))

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE MAINTENANCE_SCHEDULE
            SET STATUS = :status
            WHERE SCHEDULE_ID = :schedule_id
        """, {
            "status": status,
            "schedule_id": schedule_id
        })

        if cursor.rowcount == 0:
            flash("Schedule not found.", "error")
        else:
            connection.commit()
            flash("Schedule status updated successfully!", "success")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("schedules"))


@app.route("/spare-parts")
def spare_parts():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT PART_ID, PART_NAME, CATEGORY,
                   QUANTITY_IN_STOCK, UNIT_COST
            FROM SPARE_PART
            ORDER BY PART_ID
        """)

        parts = cursor.fetchall()

        return render_template("spare_parts.html", parts=parts)

    finally:
        cursor.close()
        connection.close()


@app.route("/spare-parts/add", methods=["POST"])
def add_spare_part():
    part_name = request.form["part_name"].strip()
    category = request.form["category"].strip()
    quantity = int(request.form["quantity"])
    unit_cost = float(request.form["unit_cost"])

    if not part_name or not category or quantity < 0 or unit_cost < 0:
        flash("Please enter valid spare part details.", "error")
        return redirect(url_for("spare_parts"))

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT NVL(MAX(PART_ID), 900) + 1
            FROM SPARE_PART
        """)
        part_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO SPARE_PART
                (PART_ID, PART_NAME, CATEGORY,
                 QUANTITY_IN_STOCK, UNIT_COST)
            VALUES
                (:part_id, :part_name, :category, :quantity, :unit_cost)
        """, {
            "part_id": part_id,
            "part_name": part_name,
            "category": category,
            "quantity": quantity,
            "unit_cost": unit_cost
        })

        connection.commit()
        flash("Spare part added successfully!", "success")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("spare_parts"))


@app.route("/spare-parts/<int:part_id>/update", methods=["POST"])
def update_spare_stock(part_id):
    quantity = int(request.form["quantity"])

    if quantity < 0:
        flash("Stock quantity cannot be negative.", "error")
        return redirect(url_for("spare_parts"))

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE SPARE_PART
            SET QUANTITY_IN_STOCK = :quantity
            WHERE PART_ID = :part_id
        """, {
            "quantity": quantity,
            "part_id": part_id
        })

        if cursor.rowcount == 0:
            flash("Spare part not found.", "error")
        else:
            connection.commit()
            flash("Stock quantity updated successfully!", "success")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("spare_parts"))

@app.route("/maintenance-records", methods=["GET", "POST"])
def maintenance_records():
    connection = None
    cursor = None
    schedules = []
    technicians = []
    records = []
    error = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        if request.method == "POST":
            schedule_id = int(request.form.get("schedule_id", ""))
            maintenance_date = request.form.get("maintenance_date", "").strip()
            issue_found = request.form.get("issue_found", "").strip()
            action_taken = request.form.get("action_taken", "").strip()
            cost_text = request.form.get("maintenance_cost", "").strip()
            check_item = request.form.get("check_item", "").strip()
            inspection_status = request.form.get("inspection_status", "").strip()
            remarks = request.form.get("remarks", "").strip()
            technician_id = int(request.form.get("technician_id", ""))

            if not all([
                maintenance_date, check_item,
                inspection_status
            ]):
                flash("Fill in the date, checklist item, and inspection status.", "error")
                return redirect(url_for("maintenance_records"))

            if inspection_status not in ("Passed", "Failed", "Needs Repair"):
                flash("Choose a valid inspection status.", "error")
                return redirect(url_for("maintenance_records"))

            if cost_text and float(cost_text) < 0:
                flash("Maintenance cost cannot be negative.", "error")
                return redirect(url_for("maintenance_records"))

            cost = float(cost_text) if cost_text else None

            # Generate IDs for this single-user project.
            cursor.execute("""
                SELECT NVL(MAX(RECORD_ID), 0) + 1
                FROM MAINTENANCE_RECORD
            """)
            record_id = cursor.fetchone()[0]

            cursor.execute("""
                SELECT NVL(MAX(CHECKLIST_ID), 0) + 1
                FROM INSPECTION_CHECKLIST
            """)
            checklist_id = cursor.fetchone()[0]

            # Table 1: create the maintenance record.
            cursor.execute("""
                INSERT INTO MAINTENANCE_RECORD
                    (RECORD_ID, SCHEDULE_ID, MAINTENANCE_DATE,
                     ISSUE_FOUND, ACTION_TAKEN, MAINTENANCE_COST)
                VALUES
                    (:record_id, :schedule_id,
                     TO_DATE(:maintenance_date, 'YYYY-MM-DD'),
                     :issue_found, :action_taken, :cost)
            """, {
                "record_id": record_id,
                "schedule_id": schedule_id,
                "maintenance_date": maintenance_date,
                "issue_found": issue_found or None,
                "action_taken": action_taken or None,
                "cost": cost
            })

            # Table 2: link the checklist item to that record.
            cursor.execute("""
                INSERT INTO INSPECTION_CHECKLIST
                    (CHECKLIST_ID, RECORD_ID, CHECK_ITEM,
                     INSPECTION_STATUS, REMARKS, TECHNICIAN_ID)
                VALUES
                    (:checklist_id, :record_id, :check_item,
                     :inspection_status, :remarks, :technician_id)
            """, {
                "checklist_id": checklist_id,
                "record_id": record_id,
                "check_item": check_item,
                "inspection_status": inspection_status,
                "remarks": remarks or None,
                "technician_id": technician_id
            })

            connection.commit()
            flash(
                f"Maintenance record #{record_id} and inspection checklist saved!",
                "success"
            )
            return redirect(url_for("maintenance_records"))

        # Only show schedules that do not already have a maintenance record.
        cursor.execute("""
            SELECT s.SCHEDULE_ID, s.TAIL_NUMBER, s.MAINTENANCE_TYPE,
                   s.SCHEDULED_DATE
            FROM MAINTENANCE_SCHEDULE s
            WHERE NOT EXISTS (
                SELECT 1
                FROM MAINTENANCE_RECORD m
                WHERE m.SCHEDULE_ID = s.SCHEDULE_ID
            )
            ORDER BY s.SCHEDULED_DATE
        """)
        schedules = cursor.fetchall()

        cursor.execute("""
            SELECT TECHNICIAN_ID, TECHNICIAN_NAME, SPECIALIZATION
            FROM MAINTENANCE_TECHNICIAN
            ORDER BY TECHNICIAN_ID
        """)
        technicians = cursor.fetchall()

        cursor.execute("""
            SELECT m.RECORD_ID, m.SCHEDULE_ID, s.TAIL_NUMBER,
                   m.MAINTENANCE_DATE, m.ISSUE_FOUND, m.ACTION_TAKEN,
                   m.MAINTENANCE_COST, c.CHECK_ITEM,
                   c.INSPECTION_STATUS, t.TECHNICIAN_NAME
            FROM MAINTENANCE_RECORD m
            JOIN MAINTENANCE_SCHEDULE s
              ON s.SCHEDULE_ID = m.SCHEDULE_ID
            LEFT JOIN INSPECTION_CHECKLIST c
              ON c.RECORD_ID = m.RECORD_ID
            LEFT JOIN MAINTENANCE_TECHNICIAN t
              ON t.TECHNICIAN_ID = c.TECHNICIAN_ID
            ORDER BY m.RECORD_ID DESC
        """)
        records = cursor.fetchall()

    except Exception as e:
        if connection:
            connection.rollback()
        error = str(e)
        if request.method == "POST":
            flash("Could not save the record. " + error, "error")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template(
        "maintenance_records.html",
        schedules=schedules,
        technicians=technicians,
        records=records,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True)

