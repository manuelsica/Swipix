from flask import render_template, request, jsonify, session
from flask_login import current_user
import uuid
from app import app, db
from models import Movie, UserPreference
from movie_data import initialize_movies
import os

import requests

RECOMMENDER_URL = os.getenv('RECOMMENDER_URL', 'http://localhost:8000')
@app.route('/')
def index():
    """
    Pagina principale dell’applicazione:
    - Se il database dei film è vuoto, chiama initialize_movies() per popolare con film di esempio.
    - Gestisce utenti autenticati e anonimi:
      * Per gli utenti autenticati, utilizza current_user.id per recuperare preferenze.
      * Per gli utenti anonimi, genera o recupera un session_id unico nella sessione.
    - Calcola quali film non sono ancora stati valutati dall’utente/sessione e li passa al template.
    - Calcola il numero di film apprezzati (liked) e lo mostra nella UI.
    """
    # Se non ci sono film nel database, inizializza con una lista predefinita
    if Movie.query.count() == 0:
        initialize_movies() #sostituire con un servizio che chiama sta funzione

    # Blocchi separati per utenti autenticati vs anonimi
    if current_user.is_authenticated:
        # Recupera gli ID dei film già valutati dall’utente corrente
        rated_movie_ids = db.session.query(UserPreference.movie_id).filter_by(
            user_id=current_user.id
        ).subquery()
        # Conta quanti film l’utente ha segnato come "mi piace"
        liked_count = UserPreference.query.filter_by(
            user_id=current_user.id,
            liked=True
        ).count()
    else:
        # Se l’utente non è autenticato, gestiamo un identificatore di sessione
        if 'session_id' not in session:
            # Genera un UUID per tracciare le preferenze dell’utente anonimo
            session['session_id'] = str(uuid.uuid4())
        session_id = session['session_id']
        # Recupera gli ID dei film già valutati per questa sessione anonima
        rated_movie_ids = db.session.query(UserPreference.movie_id).filter_by(
            session_id=session_id
        ).subquery()
        # Conta quanti film hanno ricevuto un "mi piace" in questa sessione
        liked_count = UserPreference.query.filter_by(
            session_id=session_id,
            liked=True
        ).count()

    # Seleziona tutti i film che non sono nell’elenco di quelli valutati
    # dato che sono molti, vengono presi all'inizio alcuni casuali (circa 5)
    available_movies = (Movie.query
         .filter(~Movie.id.in_(rated_movie_ids))
         .order_by(db.func.random())   # un po’ di varietà
         .limit(5)                     # max 5 card iniziali
         .all())
    
    # Mostra la pagina index.html passando i film disponibili e il conteggio dei "mi piace"
    return render_template('index.html', movies=available_movies, liked_count=liked_count)


@app.route('/rate_movie', methods=['POST'])
def rate_movie():
    """
    Endpoint AJAX per registrare la valutazione di un film (like/dislike):
    - Riceve tramite form movie_id e liked ('true' o 'false').
    - Verifica che movie_id sia stato inviato, altrimenti restituisce un errore.
    - Gestisce utenti autenticati e anonimi:
      * Controlla se la preferenza per questo film esiste già: se sì, ritorna errore.
      * Se non esiste, crea una nuova riga in UserPreference con user_id o session_id.
    - Restituisce un JSON con esito, nuovo conteggio di "mi piace" e azione effettuata.
    """
    movie_id = request.form.get('movie_id')
    liked = request.form.get('liked') == 'true'

    # Verifica che l'ID del film sia presente
    if not movie_id:
        return jsonify({'error': 'Movie ID is required'}), 400

    # Ramificazione per utenti autenticati vs anonimi
    if current_user.is_authenticated:
        # Controlla se l’utente ha già valutato questo film
        existing_preference = UserPreference.query.filter_by(
            user_id=current_user.id,
            movie_id=movie_id
        ).first()

        if existing_preference:
            # Se è già presente, segnala l’errore
            return jsonify({'error': 'Movie already rated'}), 400

        # Crea una nuova preferenza per l’utente autenticato
        preference = UserPreference()
        preference.user_id = current_user.id
        preference.movie_id = movie_id
        preference.liked = liked

        db.session.add(preference)
        db.session.commit()

        # Calcola il nuovo conteggio dei "mi piace" per l’utente
        liked_count = UserPreference.query.filter_by(
            user_id=current_user.id,
            liked=True
        ).count()
    else:
        # Gestione per utenti anonimi
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

        # Controlla se questa sessione ha già valutato il film
        existing_preference = UserPreference.query.filter_by(
            session_id=session['session_id'],
            movie_id=movie_id
        ).first()

        if existing_preference:
            return jsonify({'error': 'Movie already rated'}), 400

        # Crea nuova preferenza per l’utente anonimo
        preference = UserPreference()
        preference.session_id = session['session_id']
        preference.movie_id = movie_id
        preference.liked = liked

        db.session.add(preference)
        db.session.commit()

        # Conteggio dei "mi piace" nella sessione anonima
        liked_count = UserPreference.query.filter_by(
            session_id=session['session_id'],
            liked=True
        ).count()

    # Risposta JSON con esito e informazioni utili per l’aggiornamento front-end
    return jsonify({
        'success': True,
        'liked_count': liked_count,
        'action': 'liked' if liked else 'disliked'
    })


@app.route('/liked_movies')
def liked_movies():
    """
    Pagina che mostra l’elenco dei film contrassegnati come "mi piace":
    - Se l’utente è autenticato, filtra le preferenze con user_id e liked=True.
    - Se anonimo e non esiste session_id, mostra lista vuota.
    - Raccoglie i film associati alle preferenze trovate e rende il template liked_movies.html.
    """
    if current_user.is_authenticated:
        liked_preferences = UserPreference.query.filter_by(
            user_id=current_user.id,
            liked=True
        ).all()
    else:
        if 'session_id' not in session:
            return render_template('liked_movies.html', movies=[])

        liked_preferences = UserPreference.query.filter_by(
            session_id=session['session_id'],
            liked=True
        ).all()

    # Estrae i film dalle entries di UserPreference
    liked_movies_list = [pref.movie for pref in liked_preferences]

    return render_template('liked_movies.html', movies=liked_movies_list)


@app.route('/all_preferences')
def all_preferences():
    """
    Pagina che mostra tutti i film valutati, separando quelli "mi piace" da quelli "non mi piace":
    - Se l’utente è autenticato, filtra per user_id.
    - Se anonimo e non c’è session_id, mostra liste vuote.
    - Divide le preferenze in liked_movies e disliked_movies e le passa al template all_preferences.html.
    """
    if current_user.is_authenticated:
        all_prefs = UserPreference.query.filter_by(
            user_id=current_user.id
        ).all()
    else:
        if 'session_id' not in session:
            return render_template(
                'all_preferences.html',
                liked_movies=[],
                disliked_movies=[]
            )

        all_prefs = UserPreference.query.filter_by(
            session_id=session['session_id']
        ).all()

    # Separazione delle liste in base al valore liked
    liked_movies = [pref.movie for pref in all_prefs if pref.liked]
    disliked_movies = [pref.movie for pref in all_prefs if not pref.liked]

    return render_template(
        'all_preferences.html',
        liked_movies=liked_movies,
        disliked_movies=disliked_movies
    )


@app.route('/remove_preference/<int:movie_id>', methods=['POST'])
def remove_preference(movie_id):
    """
    Endpoint per rimuovere una preferenza esistente:
    - Accetta l’ID del film come parte dell’URL.
    - Se l’utente è autenticato, cerca la preferenza tramite user_id e movie_id.
    - Se anonimo, cerca tramite session_id e movie_id (se session_id esiste).
    - Se trovata, elimina la riga corrispondente e restituisce JSON di conferma.
    - Altrimenti, restituisce errore 404.
    """
    if current_user.is_authenticated:
        preference = UserPreference.query.filter_by(
            user_id=current_user.id,
            movie_id=movie_id
        ).first()
    elif 'session_id' in session:
        preference = UserPreference.query.filter_by(
            session_id=session['session_id'],
            movie_id=movie_id
        ).first()
    else:
        return jsonify({'error': 'No session found'}), 400

    if preference:
        db.session.delete(preference)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Preferenza rimossa!'})
    else:
        return jsonify({'error': 'Preferenza non trovata'}), 404


@app.route('/reset_preferences', methods=['POST'])
def reset_preferences():
    """
    Endpoint per resettare tutte le preferenze dell’utente o della sessione anonima:
    - Se l’utente è autenticato, elimina tutte le righe con il suo user_id.
    - Se anonimo e session_id esiste, elimina tutte le righe con quella session_id.
    - Restituisce JSON di conferma del successo.
    """
    if current_user.is_authenticated:
        UserPreference.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
    elif 'session_id' in session:
        UserPreference.query.filter_by(
            session_id=session['session_id']
        ).delete()
        db.session.commit()

    return jsonify({'success': True})

@app.route('/recommendations', methods=['POST'])
def recommendations():
    # 1) Legge il JSON dal body
    payload = request.get_json(force=True)
    app.logger.debug(f"Flask received payload: {payload!r}")

    # 2) Inoltra esattamente lo stesso JSON al microservizio FastAPI
    try:
        resp = requests.post(
            f'{RECOMMENDER_URL}/recommend',
            json=payload,
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error connecting to recommender service at {RECOMMENDER_URL}: {e}")
        return jsonify({'error': 'Service unavailable'}), 503

    app.logger.debug(f"Forwarded to FastAPI, got {resp.status_code}: {resp.text}")

    # 3) Propaga status e body al client
    try:
        data = resp.json()
    except ValueError:
        app.logger.error("Invalid JSON from recommender service")
        return jsonify({'error': 'Invalid response from recommender'}), 502

    return jsonify(data), resp.status_code