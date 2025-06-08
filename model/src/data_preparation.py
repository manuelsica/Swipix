import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer

# split dei vari generi e loro encoding che serve per trovare i film più vicini nei cluster
def preprocess_genres(df: pd.DataFrame) -> pd.DataFrame:
    df['genres'] = df['genres'].str.split('|')
    mlb = MultiLabelBinarizer()
    genre_emb = pd.DataFrame(mlb.fit_transform(df['genres']),
        columns=mlb.classes_,
        index=df.index)
    df = pd.concat([df, genre_emb], axis=1)

    return df, mlb.classes_.tolist()

# funziona prova nel test per dimezzare il carico computazionale
def filter_users(df: pd.DataFrame, n_users=10, seed=42) -> pd.DataFrame:
    users = df['userId'].unique()
    sampled_users = pd.Series(users).sample(n=min(n_users, len(users)), random_state=seed)
    filtered_df = df[df['userId'].isin(sampled_users)]
    return filtered_df


