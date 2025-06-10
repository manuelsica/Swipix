import pickle
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler
from model.src.load_data import load_data
import mlflow, time, os, subprocess, sys, platform

# --------------------------------------------------
# 1. Carica i dati di base
# --------------------------------------------------
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

mlflow.set_experiment("KNN-Recommender")

with mlflow.start_run(run_name="build_knn"):
    # parametri e contesto
    mlflow.log_params({
        "n_neighbors": 6,
        "metric":      "cosine",
        "n_users":     features_df.shape[0],
        "n_items":     features_df.shape[1],
        "git_sha":     subprocess.check_output(
                           ["git", "rev-parse", "HEAD"]).strip().decode(),
        "python":      sys.version.split()[0],
        "platform":    platform.platform()
    })

    start = time.time()
# --------------------------------------------------
# 6. Modello KNN (cosine distance)
# --------------------------------------------------
MODEL_PATH = os.path.join(os.getcwd(), 'model/knn_model.pkl')

try:
    with open(MODEL_PATH, 'rb') as f:
        knn_model = pickle.load(f)
except FileNotFoundError:
    knn_model = NearestNeighbors(n_neighbors=6, metric='cosine')
    knn_model.fit(features_df)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(knn_model, f)

# --------------------------------------------------
# 7. Esportazioni
# --------------------------------------------------
__all__ = ['knn_model', 'features_df', 'merged_df']
