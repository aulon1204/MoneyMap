# app/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Transaction, Budget, SavingsGoal
from . import db
import logging

main = Blueprint('main', __name__)

# Login
@main.route("/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        logging.debug("POST-Anfrage an /login")
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Benutzer existiert nicht.", "danger")
            logging.debug(f"Login fehlgeschlagen: Benutzer existiert nicht für Email: {email}")
            return redirect(url_for("main.user_login"))

        if not check_password_hash(user.password, password):
            flash("Falsches Passwort.", "danger")
            logging.debug(f"Login fehlgeschlagen: Falsches Passwort für Email: {email}")
            return redirect(url_for("main.user_login"))

        # Login erfolgreich
        session["user_id"] = user.id
        flash("Erfolgreich eingeloggt!", "success")
        logging.debug(f"Benutzer eingeloggt: {email}, session user_id: {session.get('user_id')}")
        return redirect(url_for("main.dashboard"))

    logging.debug("GET-Anfrage an /login")
    return render_template("login.html")

# Startseite
@main.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("main.user_login"))

# Registrierung
@main.route("/register", methods=["GET", "POST"])
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
            flash("Benutzername oder Email bereits vergeben.", "danger")
            logging.debug(f"Registrierung fehlgeschlagen: Benutzername oder Email bereits vorhanden für {username}, {email}")
            return redirect(url_for("main.register"))

        # Erstelle neuen Benutzer
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        logging.debug(f"Benutzer registriert: {username}, {email}")

        flash("Registrierung erfolgreich! Bitte melde dich an.", "success")
        return redirect(url_for("main.user_login"))
    logging.debug("GET-Anfrage an /register")
    return render_template("register.html")

# Logout
@main.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Erfolgreich abgemeldet", "success")
    logging.debug("Benutzer abgemeldet")
    return redirect(url_for("main.user_login"))

# Dashboard
@main.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Bitte melde dich an", "warning")
        logging.debug("Zugriff auf /dashboard ohne Anmeldung")
        return redirect(url_for("main.user_login"))

    user = db.session.get(User, session["user_id"])
    if user is None:
        flash("Benutzer nicht gefunden. Bitte melde dich erneut an.", "danger")
        logging.debug(f"Benutzer mit ID {session['user_id']} nicht gefunden.")
        session.pop("user_id", None)
        return redirect(url_for("main.user_login"))

    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.date.desc()).all()
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
@main.route("/add_transaction", methods=["GET", "POST"])
def add_transaction():
    if "user_id" not in session:
        flash("Bitte melde dich an, um eine Transaktion hinzuzufügen.", "warning")
        return redirect(url_for("main.user_login"))

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
            flash("Transaktion hinzugefügt!", "success")
            return redirect(url_for("main.dashboard"))
        except Exception as e:
            flash("Fehler beim Hinzufügen der Transaktion.", "danger")
            logging.error(f"Fehler beim Hinzufügen der Transaktion: {e}")
            return redirect(url_for("main.add_transaction"))
    return render_template("add_transaction.html")

# Transaktion löschen
@main.route("/delete_transaction/<int:id>", methods=["POST"])
def delete_transaction(id):
    if "user_id" not in session:
        flash("Bitte melde dich an.", "warning")
        return redirect(url_for("main.user_login"))

    transaction = Transaction.query.get_or_404(id)
    if transaction.user_id != session["user_id"]:
        flash("Zugriff verweigert.", "danger")
        return redirect(url_for("main.dashboard"))

    try:
        db.session.delete(transaction)
        db.session.commit()
        flash("Transaktion gelöscht!", "success")
    except Exception as e:
        flash("Fehler beim Löschen der Transaktion.", "danger")
        logging.error(f"Fehler beim Löschen der Transaktion: {e}")
    return redirect(url_for("main.dashboard"))

# Budget hinzufügen
@main.route("/add_budget", methods=["GET", "POST"])
def add_budget():
    if "user_id" not in session:
        flash("Bitte melde dich an, um ein Budget hinzuzufügen.", "warning")
        return redirect(url_for("main.user_login"))

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
            flash("Budget hinzugefügt!", "success")
            return redirect(url_for("main.dashboard"))
        except Exception as e:
            flash("Fehler beim Hinzufügen des Budgets.", "danger")
            logging.error(f"Fehler beim Hinzufügen des Budgets: {e}")
            return redirect(url_for("main.add_budget"))
    return render_template("add_budget.html")

# Budget löschen
@main.route("/delete_budget/<int:id>", methods=["POST"])
def delete_budget(id):
    if "user_id" not in session:
        flash("Bitte melde dich an.", "warning")
        return redirect(url_for("main.user_login"))

    budget = Budget.query.get_or_404(id)
    if budget.user_id != session["user_id"]:
        flash("Zugriff verweigert.", "danger")
        return redirect(url_for("main.dashboard"))

    try:
        db.session.delete(budget)
        db.session.commit()
        flash("Budget gelöscht!", "success")
    except Exception as e:
        flash("Fehler beim Löschen des Budgets.", "danger")
        logging.error(f"Fehler beim Löschen des Budgets: {e}")
    return redirect(url_for("main.dashboard"))

# Sparziel hinzufügen
@main.route("/add_savings_goal", methods=["GET", "POST"])
def add_savings_goal():
    if "user_id" not in session:
        flash("Bitte melde dich an, um ein Sparziel hinzuzufügen.", "warning")
        return redirect(url_for("main.user_login"))

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

            flash("Sparziel erfolgreich hinzugefügt!", "success")
            return redirect(url_for("main.dashboard"))
        except Exception as e:
            flash("Fehler beim Hinzufügen des Sparziels.", "danger")
            logging.error(f"Fehler beim Hinzufügen des Sparziels: {e}")
            return redirect(url_for("main.add_savings_goal"))
    return render_template("add_savings_goal.html")

# Sparziel löschen
@main.route("/delete_savings_goal/<int:id>", methods=["POST"])
def delete_savings_goal(id):
    if "user_id" not in session:
        flash("Bitte melde dich an.", "warning")
        return redirect(url_for("main.user_login"))

    savings_goal = SavingsGoal.query.get_or_404(id)
    if savings_goal.user_id != session["user_id"]:
        flash("Zugriff verweigert.", "danger")
        return redirect(url_for("main.dashboard"))

    try:
        db.session.delete(savings_goal)
        db.session.commit()
        flash("Sparziel gelöscht!", "success")
    except Exception as e:
        flash("Fehler beim Löschen des Sparziels.", "danger")
        logging.error(f"Fehler beim Löschen des Sparziels: {e}")
    return redirect(url_for("main.dashboard"))
