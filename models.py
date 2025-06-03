from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """
    Modello per gli utenti registrati.
    Eredita da UserMixin per integrare le funzionalità di Flask-Login
    e da db.Model per definire la tabella nel database.
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    # Username unico e obbligatorio (fino a 80 caratteri)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Email unica e obbligatoria (fino a 120 caratteri)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Hash della password (bcrypt). Lunghezza massima indicata a 256 caratteri
    password_hash = db.Column(db.String(256), nullable=False)
    # Nome e cognome opzionali (fino a 50 caratteri ciascuno)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    # Data di creazione dell’account (valorizzata automaticamente)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """
        Imposta la password dell’utente salvando l’hash generato.
        Usa Werkzeug per creare un hash sicuro a partire dalla stringa in chiaro.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verifica se la password in chiaro corrisponde all’hash salvato.
        Restituisce True se corrisponde, False altrimenti.
        """
        return check_password_hash(self.password_hash, password)

    def get_full_name(self):
        """
        Restituisce il nome completo dell’utente se first_name e last_name sono definiti.
        Altrimenti, restituisce lo username come fallback.
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

class Movie(db.Model):
    """
    Modello per i film presenti nella piattaforma.
    Contiene informazioni di base come titolo, genere, anno, ecc.
    """
    id = db.Column(db.Integer, primary_key=True)
    # Titolo del film (obbligatorio, fino a 200 caratteri)
    title = db.Column(db.String(200), nullable=False)
    # Genere del film (obbligatorio, fino a 100 caratteri)
    genre = db.Column(db.String(100), nullable=False)
    # Anno di uscita del film (obbligatorio, intero)
    year = db.Column(db.Integer, nullable=False)
    # Valutazione del film (obbligatorio, float)
    rating = db.Column(db.Float, nullable=False)
    # Descrizione testuale del film (opzionale)
    description = db.Column(db.Text)
    # URL del poster del film (opzionale, fino a 500 caratteri)
    poster_url = db.Column(db.String(500))
    # Nome del regista (opzionale, fino a 100 caratteri)
    director = db.Column(db.String(100))
    # Durata del film in minuti (opzionale, intero)
    duration = db.Column(db.Integer)
    # Data di inserimento del film nel database (valorizzata automaticamente)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserPreference(db.Model):
    """
    Modello per memorizzare le preferenze (like/dislike) di un utente o di una sessione anonima
    in relazione a un determinato film.
    """
    id = db.Column(db.Integer, primary_key=True)
    # ID dell’utente che ha espresso la preferenza (opzionale per utenti anonimi)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    # ID di sessione per utenti non autenticati (opzionale)
    session_id = db.Column(db.String(100), nullable=True)
    # ID del film a cui si riferisce la preferenza (obbligatorio)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    # Booleano che indica se l’utente ha messo “mi piace” (True) o “non mi piace” (False)
    liked = db.Column(db.Boolean, nullable=False)
    # Data di creazione della preferenza (valorizzata automaticamente)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relazione: ogni preferenza è collegata a un singolo film
    movie = db.relationship('Movie', backref='preferences')
    # Relazione: ogni preferenza può essere collegata a un singolo utente (se esiste)
    user = db.relationship('User', backref='movie_preferences')
