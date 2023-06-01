import numpy as np
import librosa 
import matplotlib as plt
import pandas as pd
from scipy.signal import butter, lfilter
import scipy.signal as signal
#import soundfile as sf
from scipy.io import wavfile





# Cargar el archivo de audio
audio, sr = librosa.load('audios/Desconocido/cry.wav',sr=44100)
cantidad_muestras=len(audio)
frecuencia_muestreo=sr

print("La cantidad de muestras de nuestro audio es:",cantidad_muestras)
print("La frecuencia de muestro de nuestro audio es:",frecuencia_muestreo)


# Obtener la duración actual del audio en segundos
duracion_actual = librosa.get_duration(y=audio,sr=sr)

print("La duracion del audio es:",duracion_actual)

if duracion_actual < 5:
    # Calcular la duración de la sección de audio silenciosa que se agregará al final
    duracion_silencio = 5 - duracion_actual

    # Calcular el número de muestras de audio silencioso que se agregarán al final
    muestras_silencio = int(duracion_silencio * sr)

    # Crear la sección de audio silenciosa
    silencio = np.zeros(muestras_silencio, dtype=audio.dtype)

    # Agregar la sección de audio silenciosa al final del archivo de audio existente
    audio_completo = np.pad(audio, (0, muestras_silencio), mode='constant')

    # Guardar el archivo de audio completo
    #sf.write('audio_completo.wav', audio_completo, sr, subtype='PCM_16')



# Calcular el tamaño de la ventana y la cantidad de muestras de "padding"
window_size = 5
alpha=3
padding_size = window_size // 2

# Agregar una ventana de "padding" al principio y al final de la señal
padding = audio_completo[:padding_size][::-1]
audio_padded = np.concatenate((padding, audio_completo, padding))


# Aplicar el filtrado SDROM
audio_filtered = np.zeros_like(audio_padded)
for i in range(window_size//2, len(audio_padded)-window_size//2):
    # Clasificar las muestras en la ventana según su magnitud
    window = audio_padded[i-window_size//2:i+window_size//2+1]
    idx = np.argsort(np.abs(window))
    ranked = window[idx]

    # Aplicar el filtro SDROM a las muestras clasificadas
    rank_mean = np.mean(ranked[1:-1])
    rank_sd = np.std(ranked[1:-1])
    thresh = rank_mean + alpha * rank_sd
    filtered_sample = ranked[0] if window[window_size//2] > thresh else rank_mean

    # Asignar la muestra filtrada a la señal de audio filtrada
    audio_filtered[i] = filtered_sample


# Aplicar SD-ROM a la señal de audio
audio_sdrom = audio_filtered
# Eliminar la ventana de "padding" de la señal resultante
audio_sdrom = audio_sdrom[padding_size:-padding_size]

# Escalar la señal resultante de vuelta a valores enteros de 16 bits si es que se va a guardar en wav
#audio_sdrom = (audio_sdrom * 32767.0).astype(np.int16)

# Guardar la señal resultante en un archivo WAV

#wavfile.write('audio_sdrom.wav', sr, audio_sdrom)


# Aplicar preénfasis
y_preemph = librosa.effects.preemphasis(audio_sdrom)

# Definir la frecuencia de corte
fc = 250

# Calcular los coeficientes del filtro Butterworth de orden 4
b, a = butter(4, fc / (sr / 2), 'highpass')

# Aplicar el filtro a la señal de audio
y_hpf = lfilter(b, a, y_preemph)

# Obtener el índice del inicio de la señal
onset = librosa.onset.onset_detect(y=y_hpf, sr=sr, units='samples')[0]

# Recortar la señal para que empiece en el inicio del llanto
y_cut = y_hpf[onset:]

# Obtener los coeficientes MFCC del archivo de audio
mfcc = librosa.feature.mfcc(y=y_cut, sr=sr, n_fft=2048,n_mels=40)

features = np.mean(mfcc.T, axis=0)





