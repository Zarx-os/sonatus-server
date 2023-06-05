# Importar librerías necesarias
import tensorflow as tf
import numpy as np
import librosa
import pandas as pd

# Leer archivo CSV
df = pd.read_csv('mfcc_data.csv')

from sklearn.model_selection import train_test_split

# Dividir los datos en conjuntos de entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(df.iloc[:, :-1], df.iloc[:, -1], test_size=0.2, random_state=42)

from keras.utils import to_categorical

# Restar 1 a las etiquetas para que estén en el rango de 0 a 2
y_train -= 1
y_test -= 1

# Convertir etiquetas a codificación one-hot
y_train = to_categorical(y_train, num_classes=3)
y_test = to_categorical(y_test, num_classes=3)

# Definir la arquitectura de la red neuronal
num_mfcc_features = X_train.shape[1]
model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(64, activation='relu', input_shape=(num_mfcc_features,)),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(3, activation='softmax')
])

model.summary()

# Compilar la red neuronal
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

# Entrenar la red neuronal
model.fit(X_train, y_train, epochs=50, batch_size=32, validation_data=(X_test, y_test))

# Evaluar el modelo
loss, acc = model.evaluate(X_test, y_test)
print("Precisión del modelo:", acc)

model.save('rednc.h5')
"""
# Hacer predicciones en nuevos datos de audio
new_audio, sr = librosa.load('nuevo.wav', sr=22050, duration=10)
new_mfccs = librosa.feature.mfcc(new_audio, sr=sr, n_mfcc=13)
prediction = model.predict_classes(new_mfccs.T)
print("La predicción de la red neuronal es:", prediction)
"""

