import numpy as np
import pandas as pd

def recommend_movies(user_id, knn_model, features_df, merged_df, top_k=5):
    # Trova indice dell'utente in features_df
    user_index = features_df.index.get_loc(user_id)
    # Recupera neighbors (includendo se stesso in posizione 0)
    distances, indices = knn_model.kneighbors(
        [features_df.iloc[user_index]],
        n_neighbors=top_k+1
    )
    # Escludi se stesso
    similar_users = features_df.index[indices[0][1:]]

    recommended_movies = {}
    # Numero di colonne corrispondenti ai generi per slicing
    n_genres = len(merged_df['genres'].str.split('|').explode().unique())

    for neighbor in similar_users:
        # Estrai rating-only profile (prime colonne)
        neighbor_ratings = features_df.loc[neighbor].iloc[:-n_genres]
        # Se rating > 3 considera "like"
        liked_movies = neighbor_ratings[neighbor_ratings > 3].index.tolist()
        for movie in liked_movies:
            recommended_movies[movie] = recommended_movies.get(movie, 0) + 1

    # Ordina per numero di segnalazioni e prendi top_k
    recommended = sorted(
        recommended_movies.items(),
        key=lambda x: x[1],
        reverse=True
    )
    return [movie_id for movie_id, _ in recommended][:top_k]