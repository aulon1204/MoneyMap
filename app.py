from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging
import os

# Logging konfigurieren
logging.basicConfig(level=logging.DEBUG)

# Flask-App initialisieren
app = Flask(__name__)

# Datenbankpfad festlegen (absolute Pfadangabe)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "finance.db"
)  # SQLite Datenbank
app.config["SECRET_KEY"] = "supersecretkey"  # Geheimschlüssel für Sessions
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Deaktiviert Warnungen

db = SQLAlchemy(app)

# Flask-Migrate initialisieren
migrate = Migrate(app, db)


# Modell für Benutzer
class User(db.Model):
    __tablename__ = "user"  # Sicherstellen, dass der Tabellenname 'user' ist
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    transactions = db.relationship("Transaction", backref="user", lazy=True)
    budgets = db.relationship("Budget", backref="user", lazy=True)
    savings_goals = db.relationship("SavingsGoal", backref="user", lazy=True)


# Login
@app.route("/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        logging.debug("POST-Anfrage an /login")
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Benutzer existiert nicht.")
            logging.debug(
                f"Login fehlgeschlagen: Benutzer existiert nicht für Email: {email}"
            )
            return redirect(url_for("user_login"))

        if not check_password_hash(user.password, password):
            flash("Falsches Passwort.")
            logging.debug(f"Login fehlgeschlagen: Falsches Passwort für Email: {email}")
            return redirect(url_for("user_login"))

        # Login erfolgreich
        session["user_id"] = user.id
        flash("Erfolgreich eingeloggt!")
        logging.debug(
            f"Benutzer eingeloggt: {email}, session user_id: {session.get('user_id')}"
        )
        return redirect(url_for("dashboard"))

    logging.debug("GET-Anfrage an /login")
    return render_template("login.html")


# Modell für Einnahmen und Ausgaben
class Transaction(db.Model):
    __tablename__ = "transaction"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    transaction_type = db.Column(
        db.String(10), nullable=False
    )  # 'income' oder 'expense'
    date = db.Column(db.DateTime, default=datetime.utcnow)
    frequency = db.Column(
        db.String(20), nullable=False, default="einmalig"
    )  # 'einmalig', 'wöchentlich', 'monatlich', 'jährlich'


# Modell für Budgets
class Budget(db.Model):
    __tablename__ = "budget"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    period = db.Column(db.String(20), nullable=False)  # z.B. 'monatlich', 'jährlich'


# Modell für Sparziele
class SavingsGoal(db.Model):
    __tablename__ = "savings_goal"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


# Startseite
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("user_login"))


# Registrierung
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        logging.debug("POST-Anfrage an /register")
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        # Überprüfen, ob Benutzer oder Email bereits existieren
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            flash("Benutzername oder Email bereits vergeben.")
            logging.debug(
                f"Registrierung fehlgeschlagen: Benutzername oder Email bereits vorhanden für {username}, {email}"
            )
            return redirect(url_for("register"))

        # Erstelle neuen Benutzer
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        logging.debug(f"Benutzer registriert: {username}, {email}")

        flash("Registrierung erfolgreich!")
        return redirect(url_for("user_login"))
    logging.debug("GET-Anfrage an /register")
    return render_template("register.html")


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Erfolgreich eingeloggt!")
            return redirect(url_for("dashboard"))
        else:
            flash("Login fehlgeschlagen. Bitte überprüfen Sie Ihre Anmeldedaten.", "danger")  # Flash-Nachricht für fehlgeschlagenes Login
            return redirect(url_for("login"))
    return render_template("login.html")


# Logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Erfolgreich abgemeldet")
    logging.debug("Benutzer abgemeldet")
    return redirect(url_for("user_login"))


# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Bitte melde dich an")
        logging.debug("Zugriff auf /dashboard ohne Anmeldung")
        return redirect(url_for("user_login"))

    user = db.session.get(User, session["user_id"])
    if user is None:
        flash("Benutzer nicht gefunden. Bitte melde dich erneut an.")
        logging.debug(f"Benutzer mit ID {session['user_id']} nicht gefunden.")
        session.pop("user_id", None)
        return redirect(url_for("user_login"))

    transactions = Transaction.query.filter_by(user_id=user.id).all()
    budgets = Budget.query.filter_by(user_id=user.id).all()
    savings_goals = SavingsGoal.query.filter_by(user_id=user.id).all()
    logging.debug(f"Dashboard geladen für Benutzer: {user.username}")
    return render_template(
        "dashboard.html",
        transactions=transactions,
        budgets=budgets,
        savings_goals=savings_goals,
    )


# Transaktion hinzufügen
@app.route("/add_transaction", methods=["GET", "POST"])
def add_transaction():
    if "user_id" not in session:
        flash("Bitte melde dich an, um eine Transaktion hinzuzufügen.")
        return redirect(url_for("user_login"))

    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
            category = request.form["category"]
            transaction_type = request.form["transaction_type"]
            frequency = request.form["frequency"]  # Das neue Feld
            user_id = session["user_id"]
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                category=category,
                transaction_type=transaction_type,
                frequency=frequency,
            )
            db.session.add(transaction)
            db.session.commit()
            flash("Transaktion hinzugefügt!")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash("Fehler beim Hinzufügen der Transaktion.")
            logging.error(f"Fehler beim Hinzufügen der Transaktion: {e}")
            return redirect(url_for("add_transaction"))
    return render_template("add_transaction.html")


# Transaktion löschen
@app.route("/delete_transaction/<int:id>", methods=["POST"])
def delete_transaction(id):
    if "user_id" not in session:
        flash("Bitte melde dich an.")
        return redirect(url_for("user_login"))

    transaction = Transaction.query.get_or_404(id)
    if transaction.user_id != session["user_id"]:
        flash("Zugriff verweigert.")
        return redirect(url_for("dashboard"))

    try:
        db.session.delete(transaction)
        db.session.commit()
        flash("Transaktion gelöscht!")
    except Exception as e:
        flash("Fehler beim Löschen der Transaktion.")
        logging.error(f"Fehler beim Löschen der Transaktion: {e}")
    return redirect(url_for("dashboard"))


# Budget hinzufügen
@app.route("/add_budget", methods=["GET", "POST"])
def add_budget():
    if "user_id" not in session:
        flash("Bitte melde dich an, um ein Budget hinzuzufügen.")
        return redirect(url_for("user_login"))

    if request.method == "POST":
        try:
            category = request.form["category"]
            amount = float(request.form["amount"])
            period = request.form["period"]
            user_id = session["user_id"]
            budget = Budget(
                user_id=user_id, category=category, amount=amount, period=period
            )
            db.session.add(budget)
            db.session.commit()
            flash("Budget hinzugefügt!")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash("Fehler beim Hinzufügen des Budgets.")
            logging.error(f"Fehler beim Hinzufügen des Budgets: {e}")
            return redirect(url_for("add_budget"))
    return render_template("add_budget.html")


# Budget löschen
@app.route("/delete_budget/<int:id>", methods=["POST"])
def delete_budget(id):
    if "user_id" not in session:
        flash("Bitte melde dich an.")
        return redirect(url_for("user_login"))

    budget = Budget.query.get_or_404(id)
    if budget.user_id != session["user_id"]:
        flash("Zugriff verweigert.")
        return redirect(url_for("dashboard"))

    try:
        db.session.delete(budget)
        db.session.commit()
        flash("Budget gelöscht!")
    except Exception as e:
        flash("Fehler beim Löschen des Budgets.")
        logging.error(f"Fehler beim Löschen des Budgets: {e}")
    return redirect(url_for("dashboard"))


# Sparziel hinzufügen
@app.route("/add_savings_goal", methods=["GET", "POST"])
def add_savings_goal():
    if "user_id" not in session:
        flash("Bitte melde dich an, um ein Sparziel hinzuzufügen.")
        return redirect(url_for("user_login"))

    if request.method == "POST":
        try:
            name = request.form["name"]
            target_amount = float(request.form["target_amount"])
            user_id = session["user_id"]

            new_goal = SavingsGoal(
                user_id=user_id, name=name, target_amount=target_amount
            )
            db.session.add(new_goal)
            db.session.commit()

            flash("Sparziel erfolgreich hinzugefügt!")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash("Fehler beim Hinzufügen des Sparziels.")
            logging.error(f"Fehler beim Hinzufügen des Sparziels: {e}")
            return redirect(url_for("add_savings_goal"))
    return render_template("add_savings_goal.html")


# Sparziel löschen
@app.route("/delete_savings_goal/<int:id>", methods=["POST"])
def delete_savings_goal(id):
    if "user_id" not in session:
        flash("Bitte melde dich an.")
        return redirect(url_for("user_login"))

    savings_goal = SavingsGoal.query.get_or_404(id)
    if savings_goal.user_id != session["user_id"]:
        flash("Zugriff verweigert.")
        return redirect(url_for("dashboard"))

    try:
        db.session.delete(savings_goal)
        db.session.commit()
        flash("Sparziel gelöscht!")
    except Exception as e:
        flash("Fehler beim Löschen des Sparziels.")
        logging.error(f"Fehler beim Löschen des Sparziels: {e}")
    return redirect(url_for("dashboard"))


# Fehlerbehandlung (optional)
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500


def process_recurring_transactions():
    today = datetime.utcnow().date()
    recurring_transactions = Transaction.query.filter(
        Transaction.frequency != None
    ).all()

    for transaction in recurring_transactions:
        if transaction.frequency == "monatlich":
            next_due_date = transaction.date + relativedelta(months=1)
        elif transaction.frequency == "jährlich":
            next_due_date = transaction.date + relativedelta(years=1)
        elif transaction.frequency == "wöchentlich":
            next_due_date = transaction.date + timedelta(weeks=1)

        if next_due_date.date() <= today:
            new_transaction = Transaction(
                user_id=transaction.user_id,
                amount=transaction.amount,
                category=transaction.category,
                transaction_type=transaction.transaction_type,
                date=datetime.utcnow(),
                frequency=transaction.frequency,
            )
            db.session.add(new_transaction)
            db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Erstellt die Datenbanktabellen, falls sie noch nicht existieren
    app.run(debug=True)
