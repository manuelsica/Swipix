import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_migrate import Migrate

# Configurazione del logging per il debug dell’applicazione
logging.basicConfig(level=logging.DEBUG)


class Base(DeclarativeBase):
    # Classe base per tutti i modelli SQLAlchemy.
    # Estende DeclarativeBase in modo che SQLAlchemy possa riconoscere tutti i model definiti.
    pass


# Inizializzazione di SQLAlchemy specificando Base come classe modello
db = SQLAlchemy(model_class=Base)
migrate = Migrate(app, db)

# Creazione dell’istanza Flask
app = Flask(__name__)

# Imposta la chiave segreta per la gestione delle sessioni:
# - Se è definita nella variabile d’ambiente SESSION_SECRET, la usa
# - Altrimenti, utilizza un valore di default che andrà cambiato in produzione
app.secret_key = os.environ.get("SESSION_SECRET", "chiave-di-default-da-cambiare-in-produzione")

# Applicazione del middleware ProxyFix:
# Questo middleware è utile quando l’app è dietro a un proxy (ad esempio Nginx)
# Permette a url_for di generare correttamente URL con https e host originali
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configurazione del database SQLite:
# - SQLALCHEMY_DATABASE_URI: specifica il percorso del file SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///swipix.db"

# Opzioni del motore SQLAlchemy per una gestione migliore delle connessioni:
# - pool_recycle: tempo (in secondi) dopo il quale riciclare una connessione
# - pool_pre_ping: verifica che la connessione sia ancora valida prima di usarla
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Inizializza SQLAlchemy con l’app Flask, in modo da poter usare 'db' per definire modelli e interagire col database
db.init_app(app)

# Configurazione di Flask-Login per gestire l’autenticazione degli utenti
login_manager = LoginManager()
login_manager.init_app(app)

# Nome della vista che gestisce il login (per redirect automatici quando serve autenticarsi)
login_manager.login_view = 'auth.login'

# Messaggio mostrato quando un utente non autenticato cerca di accedere a una pagina protetta
login_manager.login_message = 'Effettua il login per accedere a questa pagina.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    # Funzione richiesta da Flask-Login per caricare un utente a partire dal suo ID
    from models import User
    return User.query.get(int(user_id))


with app.app_context():
    # All’interno del contesto dell’applicazione, importiamo:
    # - models: dove sono definiti i modelli (come la classe User)
    # - routes: dove sono definite le rotte dell’applicazione
    import models
    import routes
    # Crea tutte le tabelle nel database se non esistono già
    db.create_all()

from prometheus_flask_exporter import Exporter
Exporter(app)


# Si importa il modulo auth dopo aver stabilito il context per evitare import circolari
import auth

if __name__ == '__main__':
    # Avvio del server Flask
    # - host '0.0.0.0' significa "ascolta su tutte le interfacce di rete"
    # - porta 5000 è la porta di default per lo sviluppo
    # - debug=True abilita il riavvio automatico e mostra eventuali errori in dettaglio
    app.run(host='0.0.0.0', port=4080, debug=True)
