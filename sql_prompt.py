"""
sql_prompt.py - a simple SQL*Plus-style prompt using python-oracledb (thin mode).
Uses the same connection settings as check_database.py / the Flask app.

Usage:   python sql_prompt.py
Then type SQL ending with ;   (type  exit  or  quit  to leave)
"""
import getpass
import oracledb

USER = "SYSTEM"
DSN = "127.0.0.1:1521/FREE"


def print_table(cursor, rows):
    headers = [d[0] for d in cursor.description]
    data = [["" if v is None else str(v) for v in row] for row in rows]
    widths = [max(len(h), *(len(r[i]) for r in data)) if data else len(h)
              for i, h in enumerate(headers)]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(line)
    print("  ".join("-" * w for w in widths))
    for r in data:
        print("  ".join(v.ljust(w) for v, w in zip(r, widths)))
    print(f"\n{len(data)} row(s) selected.\n")


def main():
    password = getpass.getpass(f"Enter password for {USER}: ")
    conn = oracledb.connect(user=USER, password=password, dsn=DSN)
    print(f"\nConnected to {DSN} as {USER}\n")

    buffer = []
    while True:
        try:
            line = input("SQL> " if not buffer else "  2  ")
        except (EOFError, KeyboardInterrupt):
            break
        stripped = line.strip()
        if not buffer and stripped.lower() in ("exit", "quit"):
            break
        if not stripped:
            continue
        buffer.append(line)
        if not stripped.endswith(";"):
            continue

        sql = "\n".join(buffer).strip().rstrip(";")
        buffer = []
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                if cur.description:
                    print_table(cur, cur.fetchall())
                else:
                    print(f"Done. {cur.rowcount} row(s) affected.\n")
        except oracledb.Error as e:
            print(f"ERROR: {e}\n")

    conn.close()
    print("Disconnected.")


if __name__ == "__main__":
    main()