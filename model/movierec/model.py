import pickle
from sklearn.neighbors import NearestNeighbors
import pandas as pd
import mlflow
import mlflow.sklearn
import os

def train_knn(features: pd.DataFrame, n_neighbors=5, experiment_name="KNN_Experiment") -> NearestNeighbors:
    
    knn = NearestNeighbors(n_neighbors=n_neighbors, metric='cosine')
    knn.fit(features)
        
        # log parametri
    mlflow.log_param("n_neighbors", n_neighbors)
    mlflow.log_param("n_features", features.shape[1])
    mlflow.log_param("n_users", features.shape[0])
        
        # log modello
    mlflow.sklearn.log_model(knn, "knn_model")
    return knn

def save_model(knn, filepath=os.path.join(os.getcwd(), "model/knn_model.pkl")):
    with open(filepath, "wb") as f:
        pickle.dump(knn, f)

def load_knn_model(filepath=os.path.join(os.getcwd(), "model/knn_model.pkl")):
    with open(filepath, "rb") as f:
        return pickle.load(f)