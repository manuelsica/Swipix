from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from models import User
import re

# Definizione di un Blueprint chiamato 'auth' per raggruppare le rotte di autenticazione
auth = Blueprint('auth', __name__)


def is_valid_email(email):
    """
    Verifica se la stringa 'email' rispetta il formato di un indirizzo email valido.
    Usa una regex semplice per controllare la presenza di username, dominio e TLD.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Gestisce la pagina di login:
    - Se l'utente è già autenticato, lo reindirizza alla home.
    - In caso di POST, valida i campi, verifica credenziali e autentica l'utente.
    """
    # Se l'utente è già loggato, evita di mostrare nuovamente il form
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Ottiene i valori inviati dal form
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))

        # Verifica campi obbligatori pieni
        if not username_or_email or not password:
            flash('Per favore inserisci username/email e password.', 'error')
            return render_template('auth/login.html')

        # Controlla se l'input somiglia a un'email o a uno username
        if is_valid_email(username_or_email):
            # Cerca l'utente per email
            user = User.query.filter_by(email=username_or_email).first()
        else:
            # Cerca l'utente per username
            user = User.query.filter_by(username=username_or_email).first()

        # Se l'utente esiste e la password corrisponde, effettua il login
        if user and user.check_password(password):
            login_user(user, remember=remember)
            # Gestisce il redirect alla pagina di destinazione, se presente
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            # In caso di credenziali errate, mostra un messaggio di errore
            flash('Credenziali non valide.', 'error')

    # Per GET o in caso di errori nel POST, renderizza il template di login
    return render_template('auth/login.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    Gestisce la pagina di registrazione:
    - Se l'utente è già autenticato, lo reindirizza alla home.
    - In caso di POST, valida i dati, controlla l'unicità di username/email,
      crea un nuovo utente e lo salva nel database.
    """
    # Se l'utente è già loggato, non permettere nuova registrazione
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Ottiene i valori inviati dal form di registrazione
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        errors = []  # Lista per raccogliere eventuali messaggi di errore

        # Validazione username: almeno 3 caratteri
        if not username or len(username) < 3:
            errors.append('Lo username deve essere di almeno 3 caratteri.')

        # Validazione email: formato corretto
        if not email or not is_valid_email(email):
            errors.append('Inserisci un indirizzo email valido.')

        # Validazione password: almeno 6 caratteri
        if not password or len(password) < 6:
            errors.append('La password deve essere di almeno 6 caratteri.')

        # Verifica corrispondenza tra password e conferma
        if password != confirm_password:
            errors.append('Le password non corrispondono.')

        # Controlla se lo username è già presente nel database
        if User.query.filter_by(username=username).first():
            errors.append('Questo username è già in uso.')

        # Controlla se l'email è già registrata
        if User.query.filter_by(email=email).first():
            errors.append('Questa email è già registrata.')

        # Se ci sono errori, li mostra con flash e mostra di nuovo il form
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')

        # Se tutti i controlli vanno a buon fine, crea un nuovo utente
        user = User()
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.set_password(password)  # Imposta la password in modo sicuro

        # Aggiunge il nuovo utente alla sessione e fa il commit sul database
        db.session.add(user)
        db.session.commit()

        # Notifica di successo e reindirizza alla pagina di login
        flash('Registrazione completata! Ora puoi accedere.', 'success')
        return redirect(url_for('auth.login'))

    # Per GET o in caso di errori, renderizza il template di registrazione
    return render_template('auth/register.html')


@auth.route('/logout')
@login_required
def logout():
    """
    Porta l'utente corrente fuori dalla sessione attiva e lo reindirizza alla home.
    Richiede che l'utente sia autenticato (decoratore @login_required).
    """
    logout_user()  # Effettua il logout
    flash('Sei stato disconnesso.', 'info')
    return redirect(url_for('index'))


# Registra il Blueprint 'auth' con prefisso '/auth' in modo che tutte le rotte
# definite sopra siano accessibili come '/auth/login', '/auth/register', ecc.
def init_app(app):
    """Register blueprint with the given Flask application."""
    app.register_blueprint(auth, url_prefix='/auth')
