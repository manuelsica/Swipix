from fastapi import FastAPI
from pydantic import BaseModel
import os
import pickle
import random, time
from typing import List, Optional

import pandas as pd
import mlflow
from mlflow.pyfunc import load_model
from mlflow.exceptions import RestException

from model.src.load_data import load_data
from model.src.data_preparation import preprocess_genres
from model.src.embeddings import compute_user_genre_preferences, create_final_features
from model.movierec.recommender import recommend_movies

# MLflow setup for inference
mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5001")
mlflow.set_tracking_uri(mlflow_uri)
mlflow.set_experiment("KNN-Recommender-Inference")

# Data loading
movies_df, ratings_df, pivot = load_data()
movies_df, genre_cols = preprocess_genres(movies_df)
ratings_with_genres = ratings_df.merge(
    movies_df[['movieId'] + genre_cols], on='movieId', how='left'
).fillna(0)
user_genre_pref = compute_user_genre_preferences(ratings_with_genres, genre_cols, 3.0)
features_df = create_final_features(pivot, user_genre_pref)

# Load model
MODEL_REGISTRY_URI = 'models:/BestKNNRecommender/Production'
LOCAL_MODEL_PATH = os.path.join(os.getcwd(), 'model/knn_best.pkl')
try:
    knn_model = load_model(MODEL_REGISTRY_URI)
except RestException:
    with open(LOCAL_MODEL_PATH, 'rb') as f:
        knn_model = pickle.load(f)

app = FastAPI()

class RequestBody(BaseModel):
    user_id: str
    top_k: int = 5
    liked_movies: Optional[List[int]] = None

@app.post('/recommend')
def recommend_api(body: RequestBody):
    start = time.time()

    # new user first phase
    if body.user_id not in features_df.index and not body.liked_movies:
        random_ids = movies_df['movieId'].sample(body.top_k).tolist()
        movie_dicts = [
            {'id': int(r['movieId']), 'title': r['title'], 'rating': r.get('rating',0),
             'genre': r['genres'], 'year': r.get('year','')}
            for _, r in movies_df[movies_df.movieId.isin(random_ids)].iterrows()
        ]
        result = {'new_user': True, 'recommendations': movie_dicts}

    # new user second phase
    elif body.user_id not in features_df.index and body.liked_movies:
        user_ratings = pd.Series(0, index=pivot.columns)
        for m in body.liked_movies:
            user_ratings[m] = 5
        user_genre = user_ratings.dot(movies_df[['movieId']+genre_cols].set_index('movieId'))
        user_genre = user_genre.div(user_genre.sum()) if user_genre.sum()>0 else user_genre
        vect = pd.concat([user_ratings, user_genre])
        aug_feats = pd.concat([features_df, vect.to_frame().T], axis=0)
        recs = recommend_movies(body.user_id, knn_model, aug_feats, movies_df, body.top_k)
        rows = movies_df[movies_df.movieId.isin(recs)]
        result = {'new_user': False, 'recommendations': [
            {'id':int(r.movieId),'title':r.title,'rating':r.get('rating',0),
             'genre':r.genres,'year':r.get('year','')} for _,r in rows.iterrows()
        ]}

    # existing user
    else:
        recs = recommend_movies(body.user_id, knn_model, features_df, movies_df, body.top_k)
        rows = movies_df[movies_df.movieId.isin(recs)]
        result = {'new_user': False, 'recommendations': [
            {'id':int(r.movieId),'title':r.title,'rating':r.get('rating',0),
             'genre':r.genres,'year':r.get('year','')} for _,r in rows.iterrows()
        ]}

    # MLflow log inference
    duration_ms = (time.time()-start)*1000
    with mlflow.start_run(nested=True):
        mlflow.log_param("user_id", body.user_id)
        mlflow.log_param("top_k", body.top_k)
        mlflow.log_metric("inference_ms", duration_ms)

    return result
