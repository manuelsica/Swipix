import pandas as pd
from sklearn.preprocessing import StandardScaler


def compute_user_genre_preferences(df: pd.DataFrame, genre_columns: list, rating_threshold=3.0) -> pd.DataFrame:
    positive_ratings = df[df['rating'] >= rating_threshold]
    user_genre_pref = positive_ratings.groupby('userId')[genre_columns].sum()
    user_genre_pref = user_genre_pref.div(user_genre_pref.sum(axis=1), axis=0).fillna(0)
    return user_genre_pref

# creazione finale della pivot table per la knn
def create_final_features(user_item_matrix: pd.DataFrame, user_genre_pref: pd.DataFrame) -> pd.DataFrame:
    
    final_features = pd.concat([user_item_matrix, user_genre_pref], axis=1).fillna(0) 
    final_features.columns = final_features.columns.astype(str)
    #standardizzazione della table
    scaler = StandardScaler()
    final_features_scaled = scaler.fit_transform(final_features)
    final_features_df = pd.DataFrame(final_features_scaled, index=final_features.index, columns=final_features.columns)
    return final_features_df

