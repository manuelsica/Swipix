# Base image
FROM python:3.9-slim
WORKDIR /app


COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


COPY model/movierec ./movierec
COPY model/src ./model/src


ENV MODEL_PATH=model/knn_model.pkl

EXPOSE 8000
CMD ["uvicorn", "movierec.api:app", "--host", "0.0.0.0", "--port", "8000"]