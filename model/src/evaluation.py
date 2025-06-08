import pandas as pd

def compute_precision_at_k(user_id, recommended_movies, ground_truth_df, k=10, threshold=4):
    relevant_movies = ground_truth_df[
        (ground_truth_df['userId'] == user_id) &
        (ground_truth_df['rating'] >= threshold)
    ]['movieId'].tolist()
    
    recommended_top_k = recommended_movies[:k]
    relevant_recommendations = set(recommended_top_k).intersection(set(relevant_movies))
    
    precision = len(relevant_recommendations) / k
    return precision

def compute_recall_at_k(user_id, recommended_movies, ground_truth_df, k=10, threshold=4):
    relevant_movies = ground_truth_df[
        (ground_truth_df['userId'] == user_id) &
        (ground_truth_df['rating'] >= threshold)
    ]['movieId'].tolist()
    
    recommended_top_k = recommended_movies[:k]
    relevant_recommendations = set(recommended_top_k).intersection(set(relevant_movies))
    
    if len(relevant_movies) == 0:
        return None  # L'utente non ha film rilevanti in test set
    recall = len(relevant_recommendations) / len(relevant_movies)
    return recall
