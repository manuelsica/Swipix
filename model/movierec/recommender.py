import numpy as np
import pandas as pd

def recommend_movies(user_id, knn_model, features_df, merged_df, top_k=5):
    user_index = features_df.index.get_loc(user_id)
    distances, indices = knn_model.kneighbors([features_df.iloc[user_index]], n_neighbors=top_k+1)
    
    similar_users = features_df.index[indices[0][1:]] #1: sta per il fatto che se stesso non deve essere preso
    
    recommended_movies = {}
    for neighbor in similar_users:
        neighbor_ratings = features_df.loc[neighbor].iloc[:-len(merged_df['genres'].explode().unique())]
        liked_movies = neighbor_ratings[neighbor_ratings > 3].index.tolist()
        for movie in liked_movies:
            if movie not in recommended_movies:
                recommended_movies[movie] = 1
            else:
                recommended_movies[movie] += 1
    
    # top-5 dei film più consigliati
    recommended_movies = sorted(recommended_movies.items(), key=lambda x: x[1], reverse=True)
    recommended_movie_ids = [movie_id for movie_id, _ in recommended_movies]
    
    return recommended_movie_ids[:top_k]
