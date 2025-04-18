from flask import Flask, render_template, request, redirect, url_for, session
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or 'your_secret_key'

# Load user data
def load_users():
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save user data
def save_users(users):
    with open('data/users.json', 'w') as f:
        json.dump(users, f, indent=4)

# Load transactions data
def load_transactions(user_id):
    try:
        with open('data/transactions.json', 'r') as f:
            transactions = json.load(f)
            return [t for t in transactions if t.get('user_id') == user_id]
    except FileNotFoundError:
        return []

# Save transactions data
def save_transactions(transactions):
    with open('data/transactions.json', 'w') as f:
        json.dump(transactions, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html', year=datetime.now().year)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('tracker'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        users = load_users()
        if any(user['username'] == username for user in users):
            return render_template('register.html', error='Username already taken')
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        users.append({'id': len(users) + 1, 'username': username, 'password': password}) # In real app, hash password
        save_users(users)
        user = next((u for u in users if u['username'] == username), None)
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('tracker'))
        else:
            return render_template('register.html', error='Registration successful, but login failed.')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('tracker'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        user = next((u for u in users if u['username'] == username and u['password'] == password), None) # In real app, compare hashed password
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('tracker'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/tracker', methods=['GET', 'POST'])
def tracker():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    user_id = session['user_id']
    transactions = load_transactions(user_id)
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    years = sorted(list(set(t['date'].split('-')[0] for t in transactions if t.get('date'))), reverse=True)

    for transaction in transactions:
        if isinstance(transaction['date'], str):
            try:
                transaction['date'] = datetime.strptime(transaction['date'], '%Y-%m-%d')
            except ValueError:
                print(f"Warning: Could not parse date string: {transaction['date']}")
                transaction['date'] = None

    selected_month = request.args.get('month')
    selected_year = request.args.get('year')

    if selected_month:
        month_num = months.index(selected_month) + 1
        transactions = [t for t in transactions if t['date'] and t['date'].year == int(selected_year) and t['date'].month == month_num]
    elif selected_year:
        transactions = [t for t in transactions if t['date'] and t['date'].year == int(selected_year)]

    transactions_for_json = []
    for t in transactions:
        transaction_copy = t.copy()
        if isinstance(transaction_copy['date'], datetime):
            transaction_copy['date'] = transaction_copy['date'].strftime('%Y-%m-%d')
        elif transaction_copy['date'] is None:
            transaction_copy['date'] = datetime.now().strftime('%Y-%m-%d')
        transaction_copy['description'] = transaction_copy.get('description', 'Unknown')
        transaction_copy['amount'] = float(transaction_copy.get('amount', 0))
        transaction_copy['type'] = transaction_copy.get('type', 'expense').lower()
        transaction_copy['category'] = transaction_copy.get('category', 'other').lower()
        transaction_copy['id'] = transaction_copy.get('id', 0)
        transaction_copy['user_id'] = transaction_copy.get('user_id', user_id)
        transactions_for_json.append(transaction_copy)

    try:
        transactions_json_string = json.dumps(transactions_for_json, ensure_ascii=False)
        print("JSON String in app.py:", transactions_json_string)
    except (TypeError, ValueError) as e:
        print(f"Error serializing JSON: {e}")
        transactions_json_string = json.dumps([])

    # Calculate totals server-side
    total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    total_spent = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    total_remaining = max(0, total_income - total_spent)

    return render_template('tracker.html', transactions=transactions, year=datetime.now().year, months=months, years=years, selected_month=selected_month, selected_year=selected_year, transactions_json_string=transactions_json_string, total_spent=total_spent, total_remaining=total_remaining)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    user_id = session['user_id']
    description = request.form['description']
    amount = float(request.form['amount'])
    type = request.form['type'].lower()
    category = request.form['category'].lower()
    transactions = load_transactions(user_id)
    transactions.append({'id': len(transactions) + 1, 'user_id': user_id, 'description': description, 'amount': amount, 'type': type, 'category': category, 'date': datetime.now().strftime('%Y-%m-%d')})
    save_transactions(transactions)
    return redirect(url_for('tracker'))

@app.route('/edit_transaction/<int:id>', methods=['GET', 'POST'])
def edit_transaction(id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    user_id = session['user_id']
    transactions = load_transactions(user_id)
    transaction = next((t for t in transactions if t['id'] == id), None)
    if not transaction:
        return redirect(url_for('tracker'))
    if request.method == 'POST':
        transaction['description'] = request.form['description']
        transaction['amount'] = float(request.form['amount'])
        transaction['type'] = request.form['type'].lower()
        transaction['category'] = request.form['category'].lower()
        save_transactions(transactions)
        return redirect(url_for('tracker'))
    return render_template('edit_transaction.html', transaction=transaction)

@app.route('/delete_transaction/<int:id>', methods=['POST'])
def delete_transaction(id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    user_id = session['user_id']
    transactions = load_transactions(user_id)
    transactions = [t for t in transactions if t['id'] != id]
    save_transactions(transactions)
    return redirect(url_for('tracker'))

if __name__ == '__main__':
    app.run(debug=True)