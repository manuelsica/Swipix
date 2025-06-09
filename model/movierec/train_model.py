#!/usr/bin/env python
"""
Standalone training script:
  1. dvc pull (se non hai i csv)
  2. prepara features_df
  3. addestra KNN
  4. logga tutto su MLflow
  5. salva knn_model.pkl
"""

import os, time, subprocess, sys, platform, pickle
import pandas as pd
import mlflow, mlflow.sklearn
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from model.src.evaluation import (
    compute_precision_at_k, compute_recall_at_k
)
from model.src.load_data import load_data
from model.movierec.recommender import recommend_movies

movies_df, ratings_df, pivot_table = load_data()
#   pivot_table: indice = userId / sessionId, colonne = movieId

# --------------------------------------------------
# 2. One-hot encoding dei generi (film × genere)
# --------------------------------------------------
genres_onehot = (
    movies_df[['movieId', 'genres']]
    .assign(genres=lambda df: df.genres.str.split('|'))
    .explode('genres')
)
genres_onehot = pd.get_dummies(genres_onehot, columns=['genres'])
genres_onehot = genres_onehot.groupby('movieId').sum()

# Assicura che gli indici abbiano lo stesso tipo (int)
pivot_table.columns = pivot_table.columns.astype(int)
genres_onehot.index = genres_onehot.index.astype(int)

# Reindicizza genres_onehot in modo che l’ordine e la lunghezza
# coincidano esattamente con le colonne di pivot_table;
# i film mancanti vengono riempiti con zeri.
genres_onehot = genres_onehot.reindex(pivot_table.columns, fill_value=0)

# --------------------------------------------------
# 3. Profilo utente sui generi  (user × film) · (film × genere)
# --------------------------------------------------
user_genre_pref = pivot_table.dot(genres_onehot)

# --------------------------------------------------
# 4. Normalizzazione 0-1 (stessa istanza di scaler per coerenza)
# --------------------------------------------------
scaler = MinMaxScaler()

user_genre_pref = pd.DataFrame(
    scaler.fit_transform(user_genre_pref),
    index=user_genre_pref.index,
    columns=user_genre_pref.columns
)

user_ratings_norm = pd.DataFrame(
    scaler.fit_transform(pivot_table.fillna(0)),
    index=pivot_table.index,
    columns=pivot_table.columns
)

# Feature finali = rating + genere
features_df = pd.concat([user_ratings_norm, user_genre_pref], axis=1)
features_df.columns = features_df.columns.astype(str)
features_df = features_df.fillna(0)
# -------------- NOVITÀ --------------\n# Indice utenti (userId / sessionId) tutto stringa → confronto uniforme
features_df.index = features_df.index.astype(str)
# ------------------------------------


# Copia di movies_df per altre funzioni (es. conteggio generi)
merged_df = movies_df.copy()

#ML FLOW TRACKINGGGG
# ---------- 3. MLflow ------------------------------------------------------
mlflow.set_experiment("KNN-Recommender")

with mlflow.start_run(run_name="train_knn") as run:
    mlflow.log_params({
        "n_neighbors": 6,
        "metric":      "cosine",
        "n_users":     features_df.shape[0],
        "n_items":     features_df.shape[1],
    })
    mlflow.set_tags({
        "git_sha": subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip(),
        "python":  sys.version.split()[0],
        "platform":platform.platform(),
    })

    t0 = time.time()
    knn = NearestNeighbors(n_neighbors=6, metric="cosine")
    knn.fit(features_df)
    mlflow.log_metric("fit_time_sec", time.time()-t0)

    # ---------- 4. evaluation ---------------------------------------------
    train_df, test_df = train_test_split(ratings_df, test_size=0.2, random_state=42)
    sample_users = test_df["userId"].unique()[:50]
    p, r = [], []
    for uid in sample_users:
        uid_str = str(uid)
        if uid_str not in features_df.index: continue
        rec_ids = recommend_movies(uid_str, knn, features_df, movies_df, top_k=5)
        p.append(compute_precision_at_k(uid, rec_ids, test_df, k=5))
        r.append(compute_recall_at_k(uid,  rec_ids, test_df, k=5))
    mlflow.log_metric("precision_at_5", sum(p)/len(p))
    mlflow.log_metric("recall_at_5",    sum(r)/len(r))

    # ---------- 5. salva modello -----------------------------------------
    pickle_path = os.path.join(os.getcwd(), 'model/knn_model.pkl')
    with open(pickle_path, "wb") as f:
        pickle.dump(knn, f)
    mlflow.sklearn.log_model(knn, artifact_path="knn_model")
    print("Model saved to", pickle_path)
