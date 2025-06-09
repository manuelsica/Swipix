
from app import db
from movie_data import initialize_movies

if __name__ == '__main__':
    with db.app.app_context():
        initialize_movies()
        print("Data ingestion completata.")