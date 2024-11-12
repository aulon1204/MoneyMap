from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Flask-App initialisieren
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'  # SQLite Datenbank
app.config['SECRET_KEY'] = 'supersecretkey'  # Geheimschlüssel für Sessions
db = SQLAlchemy(app)

# Datenbankmodelle

# Modell für Benutzer
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    budgets = db.relationship('Budget', backref='user', lazy=True)
    savings_goals = db.relationship('SavingsGoal', backref='user', lazy=True)

# Modell für Einnahmen und Ausgaben
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'income' oder 'expense'
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Modell für Budgets
class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    period = db.Column(db.String(20), nullable=False)  # z.B. 'monatlich', 'jährlich'

# Modell für Sparziele
class SavingsGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

# Startseite
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Registrierung
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        
        # Überprüfen, ob Benutzer oder Email bereits existieren
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Benutzername oder E-Mail bereits vergeben.')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registrierung erfolgreich! Bitte melde dich an.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Erfolgreich eingeloggt!')
            return redirect(url_for('dashboard'))
        flash('Login fehlgeschlagen. Bitte überprüfe deine Daten.')
    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']
        
        transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.date.desc()).all()
        budgets = Budget.query.filter_by(user_id=user_id).all()
        savings_goals = SavingsGoal.query.filter_by(user_id=user_id).all()
        
        return render_template('dashboard.html', transactions=transactions, budgets=budgets, savings_goals=savings_goals)
    
    flash('Bitte melde dich an.')
    return redirect(url_for('login'))

# Transaktion hinzufügen
@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
    if 'user_id' not in session:
        flash('Bitte melde dich an, um eine Transaktion hinzuzufügen.')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        category = request.form['category']
        transaction_type = request.form['transaction_type']
        user_id = session['user_id']
        transaction = Transaction(user_id=user_id, amount=amount, category=category, transaction_type=transaction_type)
        db.session.add(transaction)
        db.session.commit()
        flash('Transaktion hinzugefügt!')
        return redirect(url_for('dashboard'))
    return render_template('add_transaction.html')

# Transaktion löschen
@app.route('/delete_transaction/<int:id>', methods=['POST'])
def delete_transaction(id):
    if 'user_id' not in session:
        flash('Bitte melde dich an.')
        return redirect(url_for('login'))
    
    transaction = Transaction.query.get_or_404(id)
    if transaction.user_id != session['user_id']:
        flash('Zugriff verweigert.')
        return redirect(url_for('dashboard'))
    
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaktion gelöscht!')
    return redirect(url_for('dashboard'))

# Budget hinzufügen
@app.route('/add_budget', methods=['GET', 'POST'])
def add_budget():
    if 'user_id' not in session:
        flash('Bitte melde dich an, um ein Budget hinzuzufügen.')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])
        period = request.form['period']
        user_id = session['user_id']
        budget = Budget(user_id=user_id, category=category, amount=amount, period=period)
        db.session.add(budget)
        db.session.commit()
        flash('Budget hinzugefügt!')
        return redirect(url_for('dashboard'))
    return render_template('add_budget.html')

# Budget löschen
@app.route('/delete_budget/<int:id>', methods=['POST'])
def delete_budget(id):
    if 'user_id' not in session:
        flash('Bitte melde dich an.')
        return redirect(url_for('login'))
    
    budget = Budget.query.get_or_404(id)
    if budget.user_id != session['user_id']:
        flash('Zugriff verweigert.')
        return redirect(url_for('dashboard'))
    
    db.session.delete(budget)
    db.session.commit()
    flash('Budget gelöscht!')
    return redirect(url_for('dashboard'))

# Sparziel hinzufügen
@app.route('/add_savings_goal', methods=['GET', 'POST'])
def add_savings_goal():
    if 'user_id' not in session:
        flash('Bitte melde dich an, um ein Sparziel hinzuzufügen.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        target_amount = float(request.form['target_amount'])
        user_id = session['user_id']

        new_goal = SavingsGoal(
            user_id=user_id,
            name=name,
            target_amount=target_amount
        )
        db.session.add(new_goal)
        db.session.commit()

        flash('Sparziel erfolgreich hinzugefügt!')
        return redirect(url_for('dashboard'))

    return render_template('add_savings_goal.html')

# Sparziel löschen
@app.route('/delete_savings_goal/<int:id>', methods=['POST'])
def delete_savings_goal(id):
    if 'user_id' not in session:
        flash('Bitte melde dich an.')
        return redirect(url_for('login'))
    
    savings_goal = SavingsGoal.query.get_or_404(id)
    if savings_goal.user_id != session['user_id']:
        flash('Zugriff verweigert.')
        return redirect(url_for('dashboard'))
    
    db.session.delete(savings_goal)
    db.session.commit()
    flash('Sparziel gelöscht!')
    return redirect(url_for('dashboard'))

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Erfolgreich abgemeldet')
    return redirect(url_for('login'))

# Fehlerbehandlung (optional)
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Erstellt die Datenbanktabellen
    app.run(debug=True)
