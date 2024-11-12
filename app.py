from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialisiere die Flask-App
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'  # Verknüpfung zur SQLite-Datenbank
app.config['SECRET_KEY'] = 'supersecretkey'  # Schlüssel für Sitzungen
db = SQLAlchemy(app)

# Datenbankmodell für Benutzer
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Neues Modell für Einnahmen und Ausgaben
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # "income" oder "expense"
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Neues Modell für Budgets
class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    period = db.Column(db.String(20), nullable=False)  # "monthly", "yearly" oder "custom"

# Neues Modell für Sparziele
class SavingsGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

# Route zur Registrierung
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')

        # Neuen Benutzer zur Datenbank hinzufügen
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

# Route zum Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Benutzer in der Datenbank suchen
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))

        return 'Login fehlgeschlagen'

    return render_template('login.html')

# Dashboard als Beispielroute
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return 'Willkommen im Dashboard!'
    return redirect(url_for('login'))

# Route für neue Einnahmen oder Ausgaben
@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        category = request.form['category']
        transaction_type = request.form['transaction_type']
        user_id = session.get('user_id')

        transaction = Transaction(user_id=user_id, amount=amount, category=category, transaction_type=transaction_type)
        db.session.add(transaction)
        db.session.commit()
        flash('Transaktion hinzugefügt!')
        return redirect(url_for('dashboard'))
    return render_template('add_transaction.html')

# Route für ein neues Budget
@app.route('/add_budget', methods=['GET', 'POST'])
def add_budget():
    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])
        period = request.form['period']
        user_id = session.get('user_id')

        budget = Budget(user_id=user_id, category=category, amount=amount, period=period)
        db.session.add(budget)
        db.session.commit()
        flash('Budget hinzugefügt!')
        return redirect(url_for('dashboard'))
    return render_template('add_budget.html')

# Route für ein neues Sparziel
@app.route('/add_savings_goal', methods=['GET', 'POST'])
def add_savings_goal():
    if request.method == 'POST':
        name = request.form['name']
        target_amount = float(request.form['target_amount'])
        user_id = session.get('user_id')

        savings_goal = SavingsGoal(user_id=user_id, name=name, target_amount=target_amount)
        db.session.add(savings_goal)
        db.session.commit()
        flash('Sparziel hinzugefügt!')
        return redirect(url_for('dashboard'))
    return render_template('add_savings_goal.html')

# Anwendung starten
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Erstellt die Tabellen, falls sie nicht existieren
    app.run(debug=True)
