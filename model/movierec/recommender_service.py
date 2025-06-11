from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import pickle
import random, time

import pandas as pd
import mlflow
from mlflow.pyfunc import load_model
from mlflow.exceptions import RestException

from model.src.load_data import load_data
from model.src.data_preparation import preprocess_genres
from model.src.embeddings import compute_user_genre_preferences, create_final_features
from model.movierec.recommender import recommend_movies

# ───── Configuration ─────
mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5001")
mlflow.set_tracking_uri(mlflow_uri)

# ───── Data Loading & Preprocessing ─────
movies_df, ratings_df, pivot = load_data(

)
movies_df, genre_cols = preprocess_genres(movies_df)
ratings_with_genres = ratings_df.merge(
    movies_df[['movieId'] + genre_cols], on='movieId', how='left'
).fillna(0)
user_genre_pref = compute_user_genre_preferences(
    ratings_with_genres, genre_cols, rating_threshold=3.0
)
features_df = create_final_features(pivot, user_genre_pref)

# ───── Model Loading with Fallback ─────
MODEL_REGISTRY_URI = 'models:/BestKNNRecommender/Production'
LOCAL_MODEL_PATH = os.path.join(os.getcwd(), 'model/knn_model.pkl')
try:
    knn_model = load_model(MODEL_REGISTRY_URI)
    print(f"Loaded model from registry: {MODEL_REGISTRY_URI}")
except RestException:
    with open(LOCAL_MODEL_PATH, 'rb') as f:
        knn_model = pickle.load(f)
    print(f"Registry model not found, loaded local model from: {LOCAL_MODEL_PATH}")

# ───── FastAPI Service ─────
app = FastAPI()
from typing import List, Optional
class RequestBody(BaseModel):
    user_id: str
    top_k: int = 5
    # NUOVO: lista di movieId che l'utente ha messo "like" nella fase random
    liked_movies: Optional[List[int]] = None

@app.post('/recommend')
def recommend_api(body: RequestBody):
    start = time.time()
    # Primo caso: new_user senza liked_movies
    if body.user_id not in features_df.index and not body.liked_movies:
        # 5 film a caso
        random_ids = movies_df['movieId'].sample(n=body.top_k).tolist()
        movie_dicts = []
        for mid in random_ids:
            row = movies_df.loc[movies_df['movieId'] == int(mid)].iloc[0]
            movie_dicts.append({
                'id':    int(row['movieId']),
                'title': row['title'],
                'rating': row.get('rating', 0),
                'genre': row['genres'],
                'year':  row.get('year', ''),
            })
        return {'recommendations': movie_dicts, 'new_user': True}


    # Seconda chiamata: new_user con liked_movies
    if body.user_id not in features_df.index and body.liked_movies:
        # Costruisco dinamicamente un feature vector dal solo liked_movies
        # 1) riga vuota sulle colonne pivot
        user_ratings = pd.Series(0, index=pivot.columns)
        for m in body.liked_movies:
            if m in user_ratings.index:
                user_ratings[m] = 5  # rating massimo per i liked
        # 2) calcolo preferenze di genere
        user_genre = user_ratings.dot(movies_df[['movieId'] + genre_cols].set_index('movieId'))
        user_genre = user_genre.div(user_genre.sum()) if user_genre.sum()>0 else user_genre
        # 3) componi il feature vector unendo rating e genere
        vect = pd.concat([user_ratings, user_genre])
        # 4) aggiungo in coda per interrogare la KNN
        aug_feats = pd.concat([features_df, vect.to_frame().T], axis=0)
        recs = recommend_movies(
            user_id=vect.name or body.user_id,
            knn_model=knn_model,
            features_df=aug_feats,
            movies_df=movies_df,
            top_k=body.top_k
        )
        movie_dicts = []
        for mid in recs:
            row = movies_df.loc[movies_df['movieId'] == int(mid)].iloc[0]
            movie_dicts.append({
                'id':    int(row['movieId']),
                'title': row['title'],
                'rating': row.get('rating', 0),
                'genre': row['genres'],
                'year':  row.get('year', ''),
            })
        return {'recommendations': movie_dicts, 'new_user': False}

    # Caso standard: utente già presente nel modello
    recs = recommend_movies(
        user_id=body.user_id,
        knn_model=knn_model,
        features_df=features_df,
        movies_df=movies_df,
        top_k=body.top_k
    )
    # Costruisci la risposta full-blown: lista di dict con i campi che ti servono
    movie_dicts = []
    for mid in recs:
        row = movies_df.loc[movies_df['movieId'] == int(mid)].iloc[0]
        movie_dicts.append({
            'id':         int(row['movieId']),
            'title':      row['title'],
            'rating':     row.get('rating', 0),
            'genre':      row['genres'],
            'year':       row.get('year', ''),
        })

    duration_ms = (time.time() - start) * 1000
    with mlflow.start_run(nested=True):
        mlflow.log_metric("inference_ms", duration_ms)
        # Se vuoi, puoi anche loggare param user_id o top_k
        mlflow.log_param("user_id", body.user_id)
        mlflow.log_param("top_k", body.top_k)

    return {'recommendations': movie_dicts, 'new_user': False}
