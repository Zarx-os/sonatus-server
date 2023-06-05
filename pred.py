import tensorflow as tf
import pandas as pd
import numpy as np
from keras.utils import to_categorical

new_data = pd.read_csv('nuevo_audio_mfcc.csv')

model = tf.keras.models.load_model('rednc.h5')

predictions = model.predict(new_data)
predicted_classes = np.argmax(predictions, axis=1)


for prediction in predicted_classes:
    if prediction == 1:
        print("Clase predicha: hambre")
    elif prediction == 2:
        print("Clase predicha: descontento")
    else:
        print("Clase predicha desconocida")
        
print("Predicciones:", predicted_classes)

label_names = ['1', '2']  # Reemplaza con los nombres de tus clases

predicted_labels = [label_names[prediction] for prediction in predicted_classes]
print("Clases predichas:", predicted_labels)


