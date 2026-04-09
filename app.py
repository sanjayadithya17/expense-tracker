from flask import Flask, session, request, render_template, redirect
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- DB CONNECTION ----------------
def get_db():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# ---------------- INIT DB ----------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS expenses")

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # Expenses table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        amount REAL,
        category TEXT,
        date TEXT,
        description TEXT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, password)
            )
            conn.commit()
        except:
            conn.rollback()
            return "User already exists ❌"

        cur.close()
        conn.close()

        return redirect('/login')

    return render_template('signup.html')


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session['user'] = user[0]  # store user_id
            return redirect('/')
        else:
            error = "Invalid Username or Password ❌"

    return render_template('login.html', error=error)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')


# ---------------- HOME ----------------
@app.route('/')
@app.route('/home')
def index():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM expenses WHERE user_id=%s ORDER BY date DESC",
        (session['user'],)
    )
    expenses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('index.html', expenses=expenses)


# ---------------- ADD EXPENSE ----------------
@app.route('/add', methods=["GET", "POST"])
def add_expense():
    if 'user_id' not in session:   #  better check
        return redirect('/login')

    if request.method == "POST":
        amount = request.form.get('amount')
        category = request.form.get('category')
        date = request.form.get('date')
        description = request.form.get("description")
        print("Amount:",amount)
        print("Category:",category)
        print("Date:",date)
        print("Description:",description)

        #  Basic validation
        if not amount or not category or not date:
            return "All fields required ❌"

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (%s, %s, %s, %s, %s)",
            (session['user_id'], float(amount), category, date, description)
        )

        conn.commit()
        cur.close()
        conn.close()

        return redirect('/')

    return render_template('add_expense.html')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()
    cur = conn.cursor()

    selected_month = request.args.get('month')

    if selected_month:
        cur.execute(
            "SELECT * FROM expenses WHERE user_id=%s AND substring(date,1,7)=%s",
            (session['user'], selected_month)
        )
    else:
        cur.execute(
            "SELECT * FROM expenses WHERE user_id=%s",
            (session['user'],)
        )

    expenses = cur.fetchall()

    # Total
    total = sum([exp[2] for exp in expenses])  # amount index

    # Category analysis
    category_data = {}
    for exp in expenses:
        cat = exp[3]
        category_data[cat] = category_data.get(cat, 0) + exp[2]

    labels = list(category_data.keys())
    values = list(category_data.values())

    # Daily trend
    date_data = {}
    for exp in expenses:
        d = exp[4]
        date_data[d] = date_data.get(d, 0) + exp[2]

    date_labels = list(date_data.keys())
    date_values = list(date_data.values())

    # Months dropdown
    cur.execute(
        "SELECT DISTINCT substring(date,1,7) FROM expenses WHERE user_id=%s",
        (session['user'],)
    )
    months_data = cur.fetchall()
    months = [row[0] for row in months_data]

    # Insights
    insights = []

    if values:
        max_category = labels[values.index(max(values))]
        insights.append(f"You are spending more on {max_category}")

    if total > 5000:
        insights.append("Your total expense exceeded ₹5000 ⚠️")

    cur.close()
    conn.close()

    return render_template(
        'dashboard.html',
        total=total,
        labels=labels,
        values=values,
        insights=insights,
        date_labels=date_labels,
        date_values=date_values,
        months=months,
        selected_month=selected_month
    )


if __name__ == "__main__":
    app.run(debug=True)