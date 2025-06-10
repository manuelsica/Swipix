FROM python:3.9-slim

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# punta al modulo all’interno di model/movierec
CMD ["uvicorn", "model.movierec.recommender_service:app", "--host", "0.0.0.0", "--port", "8000"]
