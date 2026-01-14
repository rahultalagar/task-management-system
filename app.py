print("app.py loaded")

from flask import Flask, render_template, request, redirect, session, flash
import sqlite3


app = Flask(__name__)
app.secret_key = "secret123"

DB_NAME = "database.db"

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        description TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")


    conn.commit()
    conn.close()

init_db()

def migrate_add_status_column():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN status TEXT DEFAULT 'Pending'")
        conn.commit()
        print("Status column added")
    except sqlite3.OperationalError:
        print("Status column already exists")
    conn.close()

migrate_add_status_column()

def migrate_add_completed_at():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN completed_at TIMESTAMP")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()

migrate_add_completed_at()


from datetime import datetime, timedelta

@app.template_filter("format_datetime")
def format_datetime(value):
    if value:
        # SQLite stores UTC, convert to IST (UTC + 5:30)
        utc_time = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        ist_time = utc_time + timedelta(hours=5, minutes=30)
        return ist_time.strftime("%d %b %Y, %I:%M %p")
    return ""




# ---------- ROUTES ----------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not username or not email or not password:
            flash("Please fill all details", "error")
            return render_template("register.html")

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password)
            )
            conn.commit()
            flash("Signup successful! Redirecting to login...", "success")
            return render_template("register.html", redirect_to_login=True)
        except sqlite3.IntegrityError:
            flash("Email already registered", "error")
            return render_template("register.html")
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Email and password required", "error")
            return render_template("login.html")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )
        user = cursor.fetchone()
        conn.close()

        if not user:
            flash("Invalid email or password", "error")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        flash("Login successful! Redirecting to dashboard...", "success")
        return render_template("login.html", redirect_to_home=True)

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE user_id=? ORDER BY created_at DESC",
        (session["user_id"],)
    )
    tasks = cursor.fetchall()
    conn.close()

    return render_template("dashboard.html", tasks=tasks)


@app.route("/add-task", methods=["POST"])
def add_task():
    if "user_id" not in session:
        return redirect("/login")

    title = request.form.get("title")
    description = request.form.get("description")

    if not title:
        flash("Task title is required", "error")
        return redirect("/dashboard")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
    "INSERT INTO tasks (user_id, title, description, status) VALUES (?, ?, ?, ?)",
    (session["user_id"], title, description, "Pending")
)


    conn.commit()
    conn.close()

    flash("Task added successfully", "success")
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect("/")

@app.route("/delete-task/<int:task_id>")
def delete_task(task_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    # delete only task that belongs to logged-in user
    cursor.execute(
        "DELETE FROM tasks WHERE id=? AND user_id=?",
        (task_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    flash("Task deleted successfully", "success")
    return redirect("/dashboard")

@app.route("/complete-task/<int:task_id>")
def complete_task(task_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE tasks
        SET status='Completed',
            completed_at=CURRENT_TIMESTAMP
        WHERE id=? AND user_id=?
        """,
        (task_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    flash("Task marked as completed", "success")
    return redirect("/dashboard")

@app.route("/edit-task/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        cursor.execute(
            "UPDATE tasks SET title=?, description=? WHERE id=? AND user_id=?",
            (title, description, task_id, session["user_id"])
        )
        conn.commit()
        conn.close()

        flash("Task updated successfully", "success")
        return redirect("/dashboard")

    cursor.execute(
        "SELECT * FROM tasks WHERE id=? AND user_id=?",
        (task_id, session["user_id"])
    )
    task = cursor.fetchone()
    conn.close()

    return render_template("edit_task.html", task=task)


# ---------- RUN ----------
if __name__ == "__main__":
    print("Flask app starting...")
    app.run(debug=True, use_reloader=False)
