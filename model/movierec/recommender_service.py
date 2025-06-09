from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pickle, os
from model.src.load_data import load_data
from model.src.data_preparation import preprocess_genres, compute_user_genre_preferences, create_final_features

# Caricamento all'avvio
movies_df, ratings_df, pivot = load_data(
    movies_path="/app/model/data/movies.csv",
    ratings_path="/app/model/data/ratings.csv"
)
movies_df, genre_cols = preprocess_genres(movies_df)
features_df = create_final_features(
    pivot,
    compute_user_genre_preferences(ratings_df, genre_cols)
)
from movierec.recommender import recommend_movies

MODEL_PATH = os.path.join(os.getcwd(), 'model/knn_model.pkl')
with open(MODEL_PATH, 'rb') as f:
    knn_model = pickle.load(f)

app = FastAPI()

class RequestBody(BaseModel):
    user_id: str
    top_k: int = 5

@app.post('/recommend')
def recommend(body: RequestBody):
    if body.user_id not in features_df.index:
        raise HTTPException(status_code=404, detail="User not found")
    recs = recommend_movies(body.user_id, knn_model, features_df, movies_df)
    return {'recommendations': recs}