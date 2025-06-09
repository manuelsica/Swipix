data:
	dvc pull                           

train: data
	python model/movierec/train_model.py

serve:
	python main.py
