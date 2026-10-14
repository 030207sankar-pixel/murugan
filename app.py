from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "smart_attendance_secret_key"

DATABASE = "attendance.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT UNIQUE NOT NULL,
            student_name TEXT NOT NULL,
            department TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attendance_date TEXT NOT NULL,
            roll_number TEXT NOT NULL,
            period1 TEXT,
            period2 TEXT,
            period3 TEXT,
            period4 TEXT,
            period5 TEXT,
            UNIQUE(attendance_date, roll_number),
            FOREIGN KEY (roll_number) REFERENCES students(roll_number)
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return redirect(url_for("students_page"))


@app.route("/students", methods=["GET", "POST"])
def students_page():
    conn = get_db()

    if request.method == "POST":
        name = request.form.get("student_name", "").strip()
        department = request.form.get("department", "").strip()
        roll = request.form.get("roll_number", "").strip()

        if not name or not department or not roll:
            flash("All fields are required.")
        elif not roll.isdigit() or len(roll) < 16:
            flash("Roll number must contain at least 16 digits.")
        else:
            try:
                conn.execute(
                    """INSERT INTO students
                    (roll_number, student_name, department)
                    VALUES (?, ?, ?)""",
                    (roll, name, department)
                )
                conn.commit()
                flash("Student saved successfully!")
            except sqlite3.IntegrityError:
                flash("This roll number already exists.")

        conn.close()
        return redirect(url_for("students_page"))

    students = conn.execute(
        "SELECT * FROM students ORDER BY student_name"
    ).fetchall()

    conn.close()
    return render_template("registration.html", students=students)


@app.route("/attendance", methods=["GET", "POST"])
def attendance_page():
    conn = get_db()

    if request.method == "POST":
        date = request.form.get("attendance_date", "")

        students = conn.execute(
            "SELECT roll_number FROM students"
        ).fetchall()

        try:
            for student in students:
                roll = student["roll_number"]
                periods = []

                for i in range(1, 6):
                    value = request.form.get(f"{roll}_p{i}", "")
                    if value not in ("C", "A"):
                        raise ValueError(
                            "Select C or A for all five periods."
                        )
                    periods.append(value)

                conn.execute("""
                    INSERT INTO attendance
                    (attendance_date, roll_number, period1, period2,
                     period3, period4, period5)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(attendance_date, roll_number)
                    DO UPDATE SET
                    period1=excluded.period1,
                    period2=excluded.period2,
                    period3=excluded.period3,
                    period4=excluded.period4,
                    period5=excluded.period5
                """, (date, roll, *periods))

            conn.commit()
            flash("Attendance saved successfully!")

        except (ValueError, sqlite3.Error) as error:
            conn.rollback()
            flash(str(error))

        conn.close()
        return redirect(url_for("attendance_page",
                                date=date))

    date = request.args.get("date", "")
    students = conn.execute("""
        SELECT s.*,
               a.period1, a.period2, a.period3, a.period4, a.period5
        FROM students s
        LEFT JOIN attendance a
          ON s.roll_number = a.roll_number
         AND a.attendance_date = ?
        ORDER BY s.student_name
    """, (date,)).fetchall()

    conn.close()
    return render_template(
        "attendance.html", students=students, date=date
    )


@app.route("/dashboard")
def dashboard():
    conn = get_db()

    students = conn.execute("""
        SELECT s.roll_number, s.student_name,
               COUNT(a.id) AS recorded_days,
               SUM(
                   CASE WHEN a.id IS NOT NULL THEN
                       (a.period1='C') + (a.period2='C') +
                       (a.period3='C') + (a.period4='C') +
                       (a.period5='C')
                   ELSE 0 END
               ) AS present_periods,
               SUM(
                   CASE WHEN a.id IS NOT NULL THEN
                       (a.period1 IN ('C','A')) +
                       (a.period2 IN ('C','A')) +
                       (a.period3 IN ('C','A')) +
                       (a.period4 IN ('C','A')) +
                       (a.period5 IN ('C','A'))
                   ELSE 0 END
               ) AS total_periods
        FROM students s
        LEFT JOIN attendance a ON s.roll_number = a.roll_number
        GROUP BY s.roll_number
        ORDER BY s.student_name
    """).fetchall()

    dates = conn.execute("""
        SELECT COUNT(DISTINCT attendance_date)
        FROM attendance
    """).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html", students=students,
        completed_days=dates, remaining_days=max(0, 90 - dates)
    )


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "smart_attendance_secret_key"

DATABASE = "attendance.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT UNIQUE NOT NULL,
            student_name TEXT NOT NULL,
            department TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attendance_date TEXT NOT NULL,
            roll_number TEXT NOT NULL,
            period1 TEXT,
            period2 TEXT,
            period3 TEXT,
            period4 TEXT,
            period5 TEXT,
            UNIQUE(attendance_date, roll_number),
            FOREIGN KEY (roll_number) REFERENCES students(roll_number)
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return redirect(url_for("students_page"))


@app.route("/students", methods=["GET", "POST"])
def students_page():
    conn = get_db()

    if request.method == "POST":
        name = request.form.get("student_name", "").strip()
        department = request.form.get("department", "").strip()
        roll = request.form.get("roll_number", "").strip()

        if not name or not department or not roll:
            flash("All fields are required.")
        elif not roll.isdigit() or len(roll) < 16:
            flash("Roll number must contain at least 16 digits.")
        else:
            try:
                conn.execute(
                    """INSERT INTO students
                    (roll_number, student_name, department)
                    VALUES (?, ?, ?)""",
                    (roll, name, department)
                )
                conn.commit()
                flash("Student saved successfully!")
            except sqlite3.IntegrityError:
                flash("This roll number already exists.")

        conn.close()
        return redirect(url_for("students_page"))

    students = conn.execute(
        "SELECT * FROM students ORDER BY student_name"
    ).fetchall()

    conn.close()
    return render_template("registration.html", students=students)


@app.route("/attendance", methods=["GET", "POST"])
def attendance_page():
    conn = get_db()

    if request.method == "POST":
        date = request.form.get("attendance_date", "")

        students = conn.execute(
            "SELECT roll_number FROM students"
        ).fetchall()

        try:
            for student in students:
                roll = student["roll_number"]
                periods = []

                for i in range(1, 6):
                    value = request.form.get(f"{roll}_p{i}", "")
                    if value not in ("C", "A"):
                        raise ValueError(
                            "Select C or A for all five periods."
                        )
                    periods.append(value)

                conn.execute("""
                    INSERT INTO attendance
                    (attendance_date, roll_number, period1, period2,
                     period3, period4, period5)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(attendance_date, roll_number)
                    DO UPDATE SET
                    period1=excluded.period1,
                    period2=excluded.period2,
                    period3=excluded.period3,
                    period4=excluded.period4,
                    period5=excluded.period5
                """, (date, roll, *periods))

            conn.commit()
            flash("Attendance saved successfully!")

        except (ValueError, sqlite3.Error) as error:
            conn.rollback()
            flash(str(error))

        conn.close()
        return redirect(url_for("attendance_page",
                                date=date))

    date = request.args.get("date", "")
    students = conn.execute("""
        SELECT s.*,
               a.period1, a.period2, a.period3, a.period4, a.period5
        FROM students s
        LEFT JOIN attendance a
          ON s.roll_number = a.roll_number
         AND a.attendance_date = ?
        ORDER BY s.student_name
    """, (date,)).fetchall()

    conn.close()
    return render_template(
        "attendance.html", students=students, date=date
    )


@app.route("/dashboard")
def dashboard():
    conn = get_db()

    students = conn.execute("""
        SELECT s.roll_number, s.student_name,
               COUNT(a.id) AS recorded_days,
               SUM(
                   CASE WHEN a.id IS NOT NULL THEN
                       (a.period1='C') + (a.period2='C') +
                       (a.period3='C') + (a.period4='C') +
                       (a.period5='C')
                   ELSE 0 END
               ) AS present_periods,
               SUM(
                   CASE WHEN a.id IS NOT NULL THEN
                       (a.period1 IN ('C','A')) +
                       (a.period2 IN ('C','A')) +
                       (a.period3 IN ('C','A')) +
                       (a.period4 IN ('C','A')) +
                       (a.period5 IN ('C','A'))
                   ELSE 0 END
               ) AS total_periods
        FROM students s
        LEFT JOIN attendance a ON s.roll_number = a.roll_number
        GROUP BY s.roll_number
        ORDER BY s.student_name
    """).fetchall()

    dates = conn.execute("""
        SELECT COUNT(DISTINCT attendance_date)
        FROM attendance
    """).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html", students=students,
        completed_days=dates, remaining_days=max(0, 90 - dates)
    )


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)