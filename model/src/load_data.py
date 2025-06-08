import pandas as pd
import os

def load_sampled_movies_and_ratings(movies_path, ratings_path, n_movies=200, n_users_per_movie=40, random_seed=42):
    all_movies = pd.read_csv(movies_path)
    sampled_movies = all_movies.sample(n=n_movies, random_state=random_seed)
    sampled_movie_ids = sampled_movies['movieId'].tolist()

    ratings_iter = pd.read_csv(ratings_path, chunksize=500_000)
    ratings_chunks = []
    for chunk in ratings_iter:
        filtered_chunk = chunk[chunk['movieId'].isin(sampled_movie_ids)]
        ratings_chunks.append(filtered_chunk)
    filtered_ratings = pd.concat(ratings_chunks, ignore_index=True)

    filtered_ratings = (
        filtered_ratings
        .sort_values(['movieId', 'timestamp'])
        .groupby('movieId')
        .head(n_users_per_movie)
    )

    return sampled_movies, filtered_ratings, all_movies

def load_data(n_movies=200, n_users=40):
    movies_path   = os.path.join(os.getcwd(), "model/data/movies.csv")
    ratings_path  = os.path.join(os.getcwd(), "model/data/ratings.csv")

    sampled_movies, filtered_ratings, _ = load_sampled_movies_and_ratings(
        movies_path, ratings_path,
        n_movies=n_movies,
        n_users_per_movie=n_users,
        random_seed=42
    )

    # --------------------------------------------------------------
    # PIVOT: righe = userId, colonne = movieId, valori = rating
    # --------------------------------------------------------------
    pivot_table = (
        filtered_ratings
        .pivot_table(index="userId",
                     columns="movieId",
                     values="rating")
        .astype(float)      # assicura numerico
    )

    # opzionale: riempi i NaN con 0 se preferisci una matrice densa
    # pivot_table = pivot_table.fillna(0)

    return sampled_movies, filtered_ratings, pivot_table