from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "bank"


# DATABASE CONNECTION
def connect_db():

    conn = sqlite3.connect("bank.db")
    conn.row_factory = sqlite3.Row

    return conn


# CREATE TABLES
conn = connect_db()

# USERS TABLE
conn.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT,
    pin TEXT,
    balance INTEGER
)
""")

# HISTORY TABLE
conn.execute("""
CREATE TABLE IF NOT EXISTS history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT,
    action TEXT,
    amount INTEGER
)
""")

conn.commit()
conn.close()


# LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        fullname = request.form['fullname']
        pin = request.form['pin']

        # PIN VALIDATION
        if len(pin) != 5 or not pin.isdigit():
            return "PIN must contain exactly 5 digits"

        conn = connect_db()

        user = conn.execute(
            "SELECT * FROM users WHERE fullname=? AND pin=?",
            (fullname, pin)
        ).fetchone()

        conn.close()

        if user:

            session['user_id'] = user['id']
            session['fullname'] = user['fullname']

            return redirect('/menu')

        else:
            return "Invalid Name or PIN"

    return render_template("login.html")


# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        fullname = request.form['fullname']
        pin = request.form['pin']
        balance = request.form['balance']

        # PIN VALIDATION
        if len(pin) != 5 or not pin.isdigit():
            return "PIN must contain exactly 5 digits"

        conn = connect_db()

        conn.execute(
            "INSERT INTO users(fullname,pin,balance) VALUES(?,?,?)",
            (fullname, pin, balance)
        )

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template("register.html")


# MENU
@app.route('/menu')
def menu():

    return render_template("menu.html")


# CHECK BALANCE
@app.route('/balance')
def balance():

    conn = connect_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session['user_id'],)
    ).fetchone()

    conn.close()

    return render_template(
        "balance.html",
        balance=user['balance']
    )


# DEPOSIT MONEY
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():

    if request.method == 'POST':

        amount = int(request.form['amount'])

        conn = connect_db()

        # UPDATE BALANCE
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE id=?",
            (amount, session['user_id'])
        )

        # USER DETAILS
        user = conn.execute(
            "SELECT * FROM users WHERE id=?",
            (session['user_id'],)
        ).fetchone()

        # SAVE HISTORY
        conn.execute(
            "INSERT INTO history(fullname, action, amount) VALUES(?,?,?)",
            (user['fullname'], "Deposit", amount)
        )

        conn.commit()
        conn.close()

        return redirect('/balance')

    return render_template("deposit.html")


# WITHDRAW MONEY
@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():

    if request.method == 'POST':

        amount = int(request.form['amount'])

        conn = connect_db()

        user = conn.execute(
            "SELECT * FROM users WHERE id=?",
            (session['user_id'],)
        ).fetchone()

        # CHECK BALANCE
        if user['balance'] < amount:

            conn.close()

            return "Insufficient Balance"

        # SUBTRACT MONEY
        conn.execute(
            "UPDATE users SET balance = balance - ? WHERE id=?",
            (amount, session['user_id'])
        )

        # SAVE HISTORY
        conn.execute(
            "INSERT INTO history(fullname, action, amount) VALUES(?,?,?)",
            (user['fullname'], "Withdraw", amount)
        )

        conn.commit()
        conn.close()

        return redirect('/balance')

    return render_template("withdraw.html")


# TRANSFER MONEY
@app.route('/transfer', methods=['GET', 'POST'])
def transfer():

    if request.method == 'POST':

        receiver = request.form['receiver']
        receiver_pin = request.form['receiver_pin']
        amount = int(request.form['amount'])

        conn = connect_db()

        # SENDER
        sender = conn.execute(
            "SELECT * FROM users WHERE id=?",
            (session['user_id'],)
        ).fetchone()

        # RECEIVER
        receiver_user = conn.execute(
            "SELECT * FROM users WHERE fullname=? AND pin=?",
            (receiver, receiver_pin)
        ).fetchone()

        # RECEIVER CHECK
        if not receiver_user:

            conn.close()

            return "Receiver not found"

        # BALANCE CHECK
        if sender['balance'] < amount:

            conn.close()

            return "Insufficient Balance"

        # SUBTRACT FROM SENDER
        conn.execute(
            "UPDATE users SET balance = balance - ? WHERE id=?",
            (amount, sender['id'])
        )

        # ADD TO RECEIVER
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE id=?",
            (amount, receiver_user['id'])
        )

        # SAVE HISTORY
        conn.execute(
            "INSERT INTO history(fullname, action, amount) VALUES(?,?,?)",
            (
                sender['fullname'],
                f"Transferred to {receiver}",
                amount
            )
        )

        conn.commit()
        conn.close()

        return redirect('/balance')

    return render_template("transfer.html")


# TRANSACTION HISTORY
@app.route('/history')
def history():

    conn = connect_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session['user_id'],)
    ).fetchone()

    transactions = conn.execute(
        "SELECT * FROM history WHERE fullname=?",
        (user['fullname'],)
    ).fetchall()

    conn.close()

    return render_template(
        "history.html",
        transactions=transactions
    )


# LOGOUT
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


app.run(debug=True)