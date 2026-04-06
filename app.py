
from flask import Flask,session,request,render_template,redirect,url_for
import sqlite3

app=Flask(__name__)

def get_db():
    connection=sqlite3.connect('database.db')
    connection.row_factory=sqlite3.Row
    return connection

def init_db():
    connection=get_db()
    connection.execute(
        '''create table if not exists expenses( id integer primary key autoincrement,amount 
        real,category text,date text,description text)'''
    )
    connection.commit()
    connection.close()

init_db()

app.secret_key = "supersecretkey"   

#login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "Sanjayadithya" and password == "sanju_boomi":
            session['user'] = username
            return redirect('/')
        else:
            error = "Invalid Username or Password ❌"

    return render_template('login.html', error=error)

#logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')


#home page
@app.route("/")
@app.route("/home")
def index():
    if 'user' not in session:
        return redirect('/login')
    connection=get_db()
    expenses=connection.execute("select * from expenses order by date desc").fetchall()
    connection.close()
    return render_template('index.html',expenses=expenses)

#adding expense
@app.route('/add',methods=["GET","POST"])
def add_expense():
    if request.method=="POST":
        amount=request.form['amount']
        category=request.form['category']
        date=request.form['date']
        description=request.form["description"]

        connection=get_db()
        connection.execute(" insert into expenses(amount,category,date,description) values(?,?,?,?)",
                           (amount,category,date,description))
        connection.commit()
        connection.close()

        return redirect('/')
    return render_template('add_expense.html')

#dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    conn = get_db()

    # 👉 Get selected month from dropdown
    selected_month = request.args.get('month')

    # 👉 Filter query
    if selected_month:
        expenses = conn.execute(
            "SELECT * FROM expenses WHERE substr(date,1,7)=?",
            (selected_month,)
        ).fetchall()
    else:
        expenses = conn.execute('SELECT * FROM expenses').fetchall()

    # Total
    total = sum([exp['amount'] for exp in expenses])

    # Category analysis
    category_data = {}
    for exp in expenses:
        cat = exp['category']
        category_data[cat] = category_data.get(cat, 0) + exp['amount']

    labels = list(category_data.keys())
    values = list(category_data.values())

    print("LABELS:", labels)  
    print("VALUES:", values)

    # Daily trend data
    date_data = {}
    for exp in expenses:
        d = exp['date']
        date_data[d] = date_data.get(d, 0) + exp['amount']

    date_labels = list(date_data.keys())
    date_values = list(date_data.values())

    # 👉 Get all months for dropdown
    months_data = conn.execute(
        "SELECT DISTINCT substr(date,1,7) as month FROM expenses"
    ).fetchall()

    months = [row['month'] for row in months_data]

    # AI Insights
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


if __name__=="__main__":
    app.run(debug=True)
    
