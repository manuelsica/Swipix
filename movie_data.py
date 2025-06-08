from app import db
from models import Movie
from model.src.load_data import load_data
import pandas as pd

def initialize_movies():
    """
    Inizializza il database con una lista selezionata di film popolari.
    Ogni film è rappresentato come un dizionario con campi descrittivi.
    """

    # Elenco di film con dati reali e dettagliati
    """
    movies_data = [
        {
            'title': 'The Shawshank Redemption',
            'genre': 'Drama',
            'year': 1994,
            'rating': 9.3,
            'description': (
                'Two imprisoned men bond over a number of years, '
                'finding solace and eventual redemption through acts of common decency.'
            ),
            'poster_url': (
                'https://pixabay.com/get/g5126df99985f25a4221dc884cd43a221af5'
                '7911c20c9eff0ef4bb9c58df300d0bcee46941f0a2596dac23891b4325113e270ef6b15'
                '921eebe923c4e1496a2e58_1280.jpg'
            ),
            'director': 'Frank Darabont',
            'duration': 142
        },
        {
            'title': 'The Godfather',
            'genre': 'Crime',
            'year': 1972,
            'rating': 9.2,
            'description': (
                'The aging patriarch of an organized crime dynasty transfers '
                'control of his clandestine empire to his reluctant son.'
            ),
            'poster_url': (
                'https://pixabay.com/get/g7a80528bc336cbb3bc23c4f9e1286267b0cf55'
                '4813c64294e25c0338b1d74955a34e952773cfbeb3fcffb128e5e36ca0b08301b51937b'
                '5e5cc818e1832409599_1280.jpg'
            ),
            'director': 'Francis Ford Coppola',
            'duration': 175
        },
        {
            'title': 'The Dark Knight',
            'genre': 'Action',
            'year': 2008,
            'rating': 9.0,
            'description': (
                'When the menace known as the Joker wreaks havoc and chaos on the people of '
                'Gotham, Batman must accept one of the greatest psychological and physical tests.'
            ),
            'poster_url': (
                'https://pixabay.com/get/g1e4e8eec97df13c88cd18dad4de4c0ec9c09117'
                '14b549775c7556a57504625c742d080cdd64952da4df9800d81994b3018e6cc0109fea2cb'
                'a746e0328eabd8d2_1280.jpg'
            ),
            'director': 'Christopher Nolan',
            'duration': 152
        },
        {
            'title': 'Pulp Fiction',
            'genre': 'Crime',
            'year': 1994,
            'rating': 8.9,
            'description': (
                'The lives of two mob hitmen, a boxer, a gangster and his wife intertwine '
                'in four tales of violence and redemption.'
            ),
            'poster_url': (
                'https://pixabay.com/get/g90a1d9f0cfff22e346e29f022869a127a50bb'
                '0dfb539576959e19113b8ddfd4b3d33f7fc0acd8f7871bcc1d99c055405cbd389bc2f5253'
                '5f2716a85bd1e34d22_1280.jpg'
            ),
            'director': 'Quentin Tarantino',
            'duration': 154
        },
        {
            'title': 'Forrest Gump',
            'genre': 'Drama',
            'year': 1994,
            'rating': 8.8,
            'description': (
                'The presidencies of Kennedy and Johnson, Vietnam, Watergate, and other history unfold '
                'through the perspective of an Alabama man.'
            ),
            'poster_url': (
                'https://pixabay.com/get/gaca7c6769523250acc2df6e20494fe3080ba44'
                '10dc93053336d660b917c2aee064138b90ab182d43c5e3ab1c7c36f9648ddad2033c7eed26'
                'd6954803a26cbdb3_1280.jpg'
            ),
            'director': 'Robert Zemeckis',
            'duration': 142
        },
        {
            'title': 'Inception',
            'genre': 'Sci-Fi',
            'year': 2010,
            'rating': 8.8,
            'description': (
                'A thief who steals corporate secrets through dream-sharing technology is given '
                'the inverse task of planting an idea.'
            ),
            'poster_url': (
                'https://pixabay.com/get/g229721cc4bd65f06b7d5ef0ae97e2e0b835f2c'
                '44a968c313ec8ff5503e915f4dd8bbbff4905bf71b5805fe77fad153cbcaf54d7e589ddcd6'
                '14a6c6a20808e46a_1280.jpg'
            ),
            'director': 'Christopher Nolan',
            'duration': 148
        },
        {
            'title': 'The Matrix',
            'genre': 'Sci-Fi',
            'year': 1999,
            'rating': 8.7,
            'description': (
                'A computer programmer is led to fight an underground war against powerful computers '
                'who have constructed his entire reality.'
            ),
            'poster_url': (
                'https://pixabay.com/get/ga11e13a245bcc7a1af7368f945c61a530cba9'
                '5eae69e93913bd761e7814a36633cf4c123af9b637114454b173f6e1c57aa870a5c8026a046'
                '6265a1265043b593_1280.jpg'
            ),
            'director': 'The Wachowskis',
            'duration': 136
        },
        {
            'title': 'Goodfellas',
            'genre': 'Crime',
            'year': 1990,
            'rating': 8.7,
            'description': (
                'The story of Henry Hill and his life in the mob, covering his relationship '
                'with his wife Karen Hill e i suoi partner nella malavita.'
            ),
            'poster_url': (
                'https://pixabay.com/get/g29442430ac0aa8bde5e964e974f69fe06fe1b'
                '1827c3b2761ee0feb9456cb120e9a41a8180e8cce619b7423ec23277724d3338d548d1c368df'
                '16ca5cb2d5ecace_1280.jpg'
            ),
            'director': 'Martin Scorsese',
            'duration': 146
        },
        {
            'title': 'Interstellar',
            'genre': 'Sci-Fi',
            'year': 2014,
            'rating': 8.6,
            'description': (
                "A team of explorers travel through a wormhole in space in an attempt to ensure "
                "humanity's survival."
            ),
            'poster_url': (
                'https://pixabay.com/get/g5126df99985f25a4221dc884cd43a221af5'
                '7911c20c9eff0ef4bb9c58df300d0bcee46941f0a2596dac23891b4325113e270ef6b15921'
                'eebe923c4e1496a2e58_1280.jpg'
            ),
            'director': 'Christopher Nolan',
            'duration': 169
        },
        {
            'title': 'The Lord of the Rings: The Return of the King',
            'genre': 'Fantasy',
            'year': 2003,
            'rating': 8.9,
            'description': (
                "Gandalf and Aragorn lead the World of Men against Sauron's army to draw his gaze "
                "from Frodo and Sam."
            ),
            'poster_url': (
                'https://pixabay.com/get/g7a80528bc336cbb3bc23c4f9e1286267b0cf5'
                '54813c64294e25c0338b1d74955a34e952773cfbeb3fcffb128e5e36ca0b08301b51937b5e5'
                'cc818e1832409599_1280.jpg'
            ),
            'director': 'Peter Jackson',
            'duration': 201
        },
        {
            'title': 'Fight Club',
            'genre': 'Drama',
            'year': 1999,
            'rating': 8.8,
            'description': (
                'An insomniac office worker and a devil-may-care soap maker form an underground fight club.'
            ),
            'poster_url': (
                'https://pixabay.com/get/g1e4e8eec97df13c88cd18dad4de4c0ec9c0911'
                '714b549775c7556a57504625c742d080cdd64952da4df9800d81994b3018e6cc0109fea2cba7'
                '46e0328eabd8d2_1280.jpg'
            ),
            'director': 'David Fincher',
            'duration': 139
        },
        {
            'title': 'Star Wars: Episode V - The Empire Strikes Back',
            'genre': 'Sci-Fi',
            'year': 1980,
            'rating': 8.7,
            'description': (
                'After the Rebels are brutally overpowered by the Empire, '
                'Luke Skywalker begins Jedi training with Yoda.'
            ),
            'poster_url': (
                'https://pixabay.com/get/g90a1d9f0cfff22e346e29f022869a127a50bb'
                '0dfb539576959e19113b8ddfd4b3d33f7fc0acd8f7871bcc1d99c055405cbd389bc2f52535f'
                '2716a85bd1e34d22_1280.jpg'
            ),
            'director': 'Irvin Kershner',
            'duration': 124
        }
    ]
    """



    # Itera sulla lista di dizionari, crea un'istanza di Movie per ciascun film e la aggiunge alla sessione
    movies, ratings, pivot_table = load_data()
    #movies = list(movies)
    print(ratings.columns)
   # db.drop_all()
    #db.create_all()
    #for movie_data in movies_data:
    for _, movie_data in movies.iterrows():
        
        exist = Movie.query.filter_by(title=movie_data['title']).first()
        if exist is None:
            mean_rating = ratings[ratings['movieId'] == movie_data['movieId']]['rating'].mean() or 0.0
            year_str = movie_data['title'][-5:-1]
            movie = Movie(
                id=movie_data['movieId'],
                title=movie_data['title'],
                genre=movie_data['genres'],
                rating = 0.0 if pd.isna(mean_rating) else mean_rating,
                year = int(year_str)
            )
            db.session.add(movie)
    


    # Salva tutte le modifiche nel database
    db.session.commit()

    # Messaggio di conferma sul terminale per indicare quanti film sono stati inseriti
    print(f"Inizializzati {len(movies)} film nel database")

    #scegli i primi 5 film che l'utente deve 'recensire' per poi fare la raccomandazioni personali pian piano
    
