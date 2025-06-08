# movierec/wrapper.py
import json, joblib, numpy as np, pandas as pd, mlflow.pyfunc
from .model import MovieRec


class MovieRecWrapper(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        self.vecs   = np.load(context.artifacts["item_vecs"])
        self.movies = joblib.load(context.artifacts["movies"])
        with open(context.artifacts["genre_set"]) as f:
            genres = json.load(f)

        self.engine = MovieRec(self.vecs, self.movies, genres)

    def predict(self, ctx, model_input):
        likes    = model_input.at[0, "likes"]
        dislikes = model_input.get("dislikes", pd.Series([[]])).iat[0]
        k        = int(model_input.get("k", pd.Series([5])).iat[0])

        self.engine.likes    = likes.copy()
        self.engine.dislikes = dislikes.copy()

        recs = self.engine.recommend(k)
        #dist = self.engine.genres_list(recs.index.tolist())
        return {"recommendations": recs}
