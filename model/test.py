import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors

from src.data_preparation import preprocess_genres
from src.embeddings import compute_user_genre_preferences, create_final_features
from src.evaluation import compute_precision_at_k, compute_recall_at_k

# prova test del modello
# dataset troppo grande quindi vengono presi i primi 200 film e 40 utenti solo che hanno lasciato i rating
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


def main():

    user_id = 9999 
    n_neighbors = 3
    k_recommendations = 5
    threshold_rating = 4


    movies_path = "/Users/ludovicagenovese/Documents/GitHub/Swipix/model/data/movies.csv"
    ratings_path = "/Users/ludovicagenovese/Documents/GitHub/Swipix/model/data/ratings.csv"

    sampled_movies, filtered_ratings, all_movies = load_sampled_movies_and_ratings(
        movies_path, ratings_path,
        n_movies=200,
        n_users_per_movie=40,
        random_seed=42
    )


    sampled_movies['movieId'] = sampled_movies['movieId'].astype(str)
    filtered_ratings['movieId'] = filtered_ratings['movieId'].astype(str)


    print("🎬 Film selezionati:")
    print(sampled_movies[['movieId', 'title']])


    selected_movies = sampled_movies.sample(n=5)
    user_ratings_data = [
        {'userId': user_id, 'movieId': row['movieId'], 'rating': np.random.randint(6, 10)}
        for _, row in selected_movies.iterrows()
    ]
    user_ratings = pd.DataFrame(user_ratings_data)

    print("\n⭐️ Ratings simulati per l'utente:")
    for row in user_ratings.itertuples(index=False):
        movie_title = sampled_movies.loc[sampled_movies['movieId'] == row.movieId, 'title'].values[0]
        print(f" - {movie_title} (ID: {row.movieId}) -> rating: {row.rating}")


    ratings_with_user = pd.concat([filtered_ratings, user_ratings], ignore_index=True)
    merged = ratings_with_user.merge(sampled_movies, on='movieId')
    merged['movieId'] = merged['movieId'].astype(str)

    merged, genre_columns = preprocess_genres(merged)

    user_item_matrix = merged.pivot_table(index='userId', columns='movieId', values='rating').fillna(0)
    user_item_matrix.columns = user_item_matrix.columns.astype(str)
    user_item_matrix = user_item_matrix.loc[:, user_item_matrix.columns.isin(sampled_movies['movieId'])]
    user_genre_pref = compute_user_genre_preferences(merged, genre_columns)
    final_features = create_final_features(user_item_matrix, user_genre_pref)

    knn_model = NearestNeighbors(n_neighbors=n_neighbors, metric='euclidean')
    knn_model.fit(final_features)


    user_index = final_features.index.get_loc(user_id)
    distances, indices = knn_model.kneighbors([final_features.iloc[user_index]], n_neighbors=n_neighbors+1)

    similar_users = final_features.index[indices[0][1:]]
    recommended_movies = {}
    for neighbor in similar_users:
        neighbor_ratings = final_features.loc[neighbor].iloc[:-len(genre_columns)]
        liked_movies = neighbor_ratings[neighbor_ratings > 3].index.tolist()
        for movie in liked_movies:
            recommended_movies[movie] = recommended_movies.get(movie, 0) + 1

    recommended_movies = sorted(recommended_movies.items(), key=lambda x: x[1], reverse=True)
    recommended_movie_ids = [str(movie_id) for movie_id, _ in recommended_movies][:k_recommendations]


    print(f"Film raccomandati per l'utente {user_id}:")
    movie_lookup = dict(sampled_movies[['movieId', 'title']].drop_duplicates().values)
    if recommended_movie_ids:
        for mid in recommended_movie_ids:
            title = movie_lookup.get(mid, "Unknown Title")
            print(f" - {title} (ID: {mid})")
    else:
        print("Nessun film consigliato.")

    # computazione metriche precision e recall @ 5 in questo caso
    precision_at_k = compute_precision_at_k(user_id, recommended_movie_ids, merged, k=k_recommendations, threshold=threshold_rating)
    recall_at_k = compute_recall_at_k(user_id, recommended_movie_ids, merged, k=k_recommendations, threshold=threshold_rating)

    print(f"\n📈 Precision@{k_recommendations}: {precision_at_k:.4f}" if precision_at_k is not None else "📈 Precision@5: N/A")
    print(f"📈 Recall@{k_recommendations}: {recall_at_k:.4f}" if recall_at_k is not None else "📈 Recall@5: N/A")

if __name__ == "__main__":
    main()
