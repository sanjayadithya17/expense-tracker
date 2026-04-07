from flask import Flask,session,request,render_template,redirect,url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"

# DB CONNECTION
def get_db():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

#  INIT DB (UPDATED FOR MULTI USER)
def init_db():
    connection = get_db()

    #  USERS TABLE
    connection.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # EXPENSE TABLE (UPDATED with user_id)
    connection.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        category TEXT,
        date TEXT,
        description TEXT
    )
    """)

    connection.commit()
    connection.close()

#  CALL INIT
init_db()

#-------------- Signup-----------------
@app.route('/signup', methods=['GET','POST'])
def signup():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
            conn.close()

            return redirect('/login')

        except:
            error = "Username already exists ❌"

    return render_template('signup.html', error=error)
# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        conn.close()

        if user:
            session['user_id'] = user['id']   
            session['user'] = user['username']
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
@app.route("/")
@app.route("/home")
def index():
    if 'user' not in session:
        return redirect('/login')
    user_id=session['user_id']

    connection = get_db()

    # user_id filter
    expenses = connection.execute(
        "SELECT * FROM expenses WHERE user_id=? ORDER BY date DESC",(user_id,)
    ).fetchall()

    connection.close()
    return render_template('index.html', expenses=expenses)


# ---------------- ADD EXPENSE ----------------
@app.route('/add', methods=["GET","POST"])
def add_expense():
    if request.method == "POST":
        amount = request.form['amount']
        category = request.form['category']
        date = request.form['date']
        description = request.form["description"]
        user_id=session['user_id']

        connection = get_db()
        connection.execute(
            "INSERT INTO expenses(user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description)
        )

        connection.commit()
        connection.close()

        return redirect('/')

    return render_template('add_expense.html')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()

    user_id = session['user_id']   

    selected_month = request.args.get('month')

    # Filter expenses (USER + MONTH)
    if selected_month:
        expenses = conn.execute(
            "SELECT * FROM expenses WHERE user_id=? AND substr(date,1,7)=?",
            (user_id, selected_month)
        ).fetchall()
    else:
        expenses = conn.execute(
            "SELECT * FROM expenses WHERE user_id=?",
            (user_id,)
        ).fetchall()

    # Total
    total = sum([exp['amount'] for exp in expenses])

    #  Category analysis
    category_data = {}
    for exp in expenses:
        cat = exp['category']
        category_data[cat] = category_data.get(cat, 0) + exp['amount']

    labels = list(category_data.keys())
    values = list(category_data.values())

    #  Daily trend
    date_data = {}
    for exp in expenses:
        d = exp['date']
        date_data[d] = date_data.get(d, 0) + exp['amount']

    date_labels = list(date_data.keys())
    date_values = list(date_data.values())

    #  Months dropdown (USER BASED)
    months_data = conn.execute(
        "SELECT DISTINCT substr(date,1,7) as month FROM expenses WHERE user_id=?",
        (user_id,)
    ).fetchall()

    months = [row['month'] for row in months_data]

    #  AI Insights
    insights = []

    if values:
        max_category = labels[values.index(max(values))]
        insights.append(f"You are spending more on {max_category}")

    if total > 5000:
        insights.append("Your total expense exceeded ₹5000 ⚠️")

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