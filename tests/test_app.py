import sys
import os
import pytest
from werkzeug.security import generate_password_hash

# Projektwurzel zum Python-Pfad hinzufügen
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, User, Transaction, Budget, SavingsGoal

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-Memory-Datenbank für Tests
    app.config['WTF_CSRF_ENABLED'] = False  # Deaktiviert CSRF für Tests
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Erstelle einen Testbenutzer mit gehashtem Passwort
            test_user = User(
                username='testuser',
                email='test@example.com',
                password=generate_password_hash('password123', method='pbkdf2:sha256')
            )
            db.session.add(test_user)
            db.session.commit()
        yield client
        with app.app_context():
            db.drop_all()

def login(client, email, password):
    return client.post('/login', data=dict(
        email=email,
        password=password
    ), follow_redirects=True)

def test_home_redirects_to_login(client):
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_register(client):
    response = client.post('/register', data=dict(
        username='newuser',
        email='newuser@example.com',
        password='newpassword'
    ), follow_redirects=True)
    assert b'Registrierung erfolgreich!' in response.data  # Mit Ausrufezeichen

def test_login_logout(client):
    # Anmelden mit korrektem Passwort
    response = login(client, 'test@example.com', 'password123')
    assert b'Erfolgreich eingeloggt!' in response.data

    # Abmelden
    response = client.get('/logout', follow_redirects=True)
    assert b'Erfolgreich abgemeldet' in response.data

    # Anmelden mit falschem Passwort
    response = login(client, 'test@example.com', 'wrongpassword')
    assert b'Login fehlgeschlagen' in response.data

def test_dashboard_access(client):
    # Zugriff ohne Login
    response = client.get('/dashboard', follow_redirects=True)
    assert b'Bitte melde dich an' in response.data

    # Zugriff mit Login
    response = login(client, 'test@example.com', 'password123')
    assert b'Erfolgreich eingeloggt!' in response.data

    response = client.get('/dashboard')
    assert b'Deine Transaktionen' in response.data
    assert b'Deine Budgets' in response.data
    assert b'Deine Sparziele' in response.data
