# AeroMaintain — Aviation Maintenance Management System

AeroMaintain is a web-based Aviation Maintenance Management System developed as a Database Management Systems (DBMS) project. It helps manage aircraft information, maintenance schedules, maintenance records, inspection checklists, spare parts, and maintenance alerts through a simple web interface connected to an Oracle Database.

## Project Overview

Aircraft maintenance requires organized records, scheduled inspections, technician assignments, and spare-part tracking. AeroMaintain provides a centralized application to manage these operations and maintain consistency between related database records.

## Features

- **Dashboard:** View a summary of aircraft, hangar facilities, technicians, maintenance schedules, spare parts, and alerts.
- **Aircraft Management:** Add, view, edit, and delete aircraft information.
- **Maintenance Scheduling:** Create maintenance schedules, assign technicians, and update schedule status.
- **Maintenance Records:** Record maintenance activities, issues found, actions taken, maintenance costs, and inspection checklist details.
- **Spare-Part Management:** View spare-part inventory and update stock quantities.
- **Oracle Database Integration:** Execute database operations through Flask routes and SQL queries.
- **Input Validation:** Validate submitted data and handle database errors.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web framework and routing |
| HTML5 | Frontend structure |
| CSS3 | User interface styling |
| Jinja2 | Dynamic HTML templates |
| Oracle Database | Relational data storage |
| python-oracledb | Python-to-Oracle connectivity |
| python-dotenv | Loading database configuration from environment variables |
| Git and GitHub | Version control and project hosting |

## Database Design

The project uses nine main database tables.

| Table Name | Purpose |
|---|---|
| `AIRCRAFT_LOG` | Stores aircraft details |
| `HANGAR_FACILITY` | Stores hangar and facility information |
| `MAINTENANCE_TECHNICIAN` | Stores technician details and qualifications |
| `MAINTENANCE_SCHEDULE` | Stores scheduled maintenance activities |
| `MAINTENANCE_RECORD` | Stores completed maintenance details |
| `INSPECTION_CHECKLIST` | Stores inspection items and their results |
| `SPARE_PART` | Stores spare-part information and stock |
| `PART_USAGE` | Tracks parts used during maintenance |
| `MAINTENANCE_ALERT` | Stores maintenance-related alerts |

The database uses relational constraints, including primary keys and foreign keys, to maintain data integrity. Additional unique and check constraints are applied where defined in the database schema.

## Project Structure

```text
Dbms_aviation/
├── app.py
├── db.py
├── .env                 # Local database credentials; not committed
├── .gitignore
├── requirements.txt
├── templates/
│   ├── dashboard.html
│   ├── aircraft.html
│   ├── aircraft_edit.html
│   ├── schedules.html
│   ├── spare_parts.html
│   └── maintenance_records.html
└── static/
    └── style.css
```

This structure reflects the main application files. Include any additional SQL scripts or templates that exist in your repository.

## Prerequisites

Before running the application, make sure you have:

- Python installed
- Oracle Database installed and running
- Git installed
- The project source code
- Oracle database credentials with access to the required tables

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/Dbms_aviation.git
cd Dbms_aviation
```

Replace `YOUR-USERNAME` with your GitHub username.

### 2. Create a virtual environment

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use Command Prompt instead:

```cmd
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure the database connection

Create a local `.env` file in the project root:

```env
DB_USER=SYSTEM
DB_PASSWORD=YOUR_ORACLE_PASSWORD
DB_DSN=127.0.0.1:1521/FREE
```

Replace the example password with your own Oracle password. The Oracle service name and credentials must match your local database configuration.

**Security:** Never commit your `.env` file or publish your database password.

### 5. Run the application

```bash
python app.py
```

Open the following address in your browser:

```text
http://127.0.0.1:5000
```

The Oracle Database service must be running, and the required database tables must exist before using the application.

## Database Connectivity

AeroMaintain uses Flask to handle browser requests and `python-oracledb` to communicate with Oracle Database.

1. A user interacts with a frontend form.
2. Flask receives the submitted data.
3. The backend establishes a database connection through `db.py`.
4. SQL statements retrieve or modify the relevant database records.
5. The backend commits successful changes and returns the updated page or a status message.

## Future Enhancements

- Automated maintenance reminders based on flight hours and scheduled dates.
- Improved spare-part usage and inventory tracking.
- Role-based access for administrators and maintenance technicians.
- Maintenance history reports and analytics.
- More comprehensive validation and audit logging.

## Academic Project

**Project Name:** AeroMaintain — Aviation Maintenance Management System  
**Project Type:** Database Management Systems (DBMS)  
**Backend:** Python and Flask  
**Database:** Oracle Database

Developed for academic learning and demonstration of relational database design, SQL operations, backend connectivity, and web application development.