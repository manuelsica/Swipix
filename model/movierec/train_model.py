#!/usr/bin/env python
"""
Grid-search training script:
  1. dvc pull (se non hai i csv)
  2. prepara features_df
  3. esplora coppie (k, metric)
  4. logga ogni run su MLflow
  5. salva e registra il miglior modello
"""

import os
import time
import pickle
import subprocess
import sys
import platform

import pandas as pd
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

from model.src.load_data import load_data
from model.src.data_preparation import preprocess_genres
from model.src.embeddings import compute_user_genre_preferences, create_final_features
from model.movierec.recommender import recommend_movies
from model.src.evaluation import compute_precision_at_k, compute_recall_at_k

# ───────────── MLflow setup ─────────────
mlflow.set_tracking_uri("http://mlflow:5001")
mlflow.set_experiment("KNN-Recommender-GridSearch")

# ───────────── Caricamento dati ─────────────
movies_df, ratings_df, pivot = load_data(
   
)
movies_df, genre_cols = preprocess_genres(movies_df)

# Unione ratings ⇄ generi
ratings_with_genres = ratings_df.merge(
    movies_df[['movieId'] + genre_cols],
    on='movieId',
    how='left'
).fillna(0)

# Calcolo preferenze utente × genere
user_genre_pref = compute_user_genre_preferences(
    ratings_with_genres,
    genre_cols,
    rating_threshold=3.0
)

# Matrice finale di feature
features_df = create_final_features(pivot, user_genre_pref)

# Split evaluation
df_train, df_test = train_test_split(ratings_df, test_size=0.2, random_state=42)
sample_users = df_test['userId'].unique()[:50]

# ───────────── Grid-search ─────────────
param_grid = {
    'n_neighbors': [4, 6, 8, 10],
    'metric': ['cosine', 'euclidean']
}

best_score = -1.0
best_run_id = None
best_k, best_metric = None, None

for k in param_grid['n_neighbors']:
    for metric in param_grid['metric']:
        run_name = f"k={k}|metric={metric}"
        with mlflow.start_run(run_name=run_name):
            # Log parametri
            mlflow.log_params({'n_neighbors': k, 'metric': metric})

            # Addestramento
            knn = NearestNeighbors(n_neighbors=k, metric=metric)
            t0 = time.time()
            knn.fit(features_df)
            mlflow.log_metric("fit_time_sec", time.time() - t0)

            # Evaluation
            precisions, recalls = [], []
            for uid in sample_users:
                uid_str = str(uid)
                if uid_str not in features_df.index:
                    continue
                recs = recommend_movies(uid_str, knn, features_df, movies_df, top_k=5)
                precisions.append(compute_precision_at_k(uid, recs, df_test, k=5))
                recalls.append(compute_recall_at_k(uid, recs, df_test, k=5))

            precision = sum(precisions) / len(precisions) if precisions else 0.0
            recall = sum(recalls) / len(recalls) if recalls else 0.0
            mlflow.log_metrics({
                'precision_at_5': precision,
                'recall_at_5': recall
            })

            # Aggiorna best model (priorità a precision)
            if precision > best_score:
                best_score = precision
                best_run_id = mlflow.active_run().info.run_id
                best_k, best_metric = k, metric
                # Salva snapshot del modello
                with open("knn_best.pkl", "wb") as f:
                    pickle.dump(knn, f)

# ───────────── Registra il miglior modello ─────────────
if best_run_id:
    # Carica il pickle come artefatto nel run migliore
    mlflow.log_artifact("knn_best.pkl", artifact_path="best_model")

    # URI del modello nel run
    model_uri = f"runs:/{best_run_id}/best_model/knn_best.pkl"

    # Registra e promuovi in Production
    registered = mlflow.register_model(model_uri, "BestKNNRecommender")
    client = MlflowClient()
    client.transition_model_version_stage(
        name="BestKNNRecommender",
        version=registered.version,
        stage="Production"
    )

    print(f"Best model: k={best_k}, metric={best_metric}, run_id={best_run_id}")

# ───────────── Fine ─────────────
