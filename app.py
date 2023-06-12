import mysql.connector
import json, uuid, wave, librosa, os, io, pickle, random,string
from flask import Flask, request, jsonify, send_file,make_response
from io import BytesIO
from flask_cors import CORS
from base64 import b64encode
import numpy as np
import matplotlib as plt
import pandas as pd
from scipy.signal import butter, lfilter
import scipy.signal as signal
from scipy.io import wavfile
import tensorflow as tf
import pandas as pd
import numpy as np
from keras.utils import to_categorical
import soundfile as sf
from flask_mail import Mail, Message

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'fpvqazbzfr',
    'password': '710CKR3MECR7G4N5$',
    'database': 'sonatus-database',
    'port':'3306'
}


app.config.from_pyfile('config.py')  # Carga la configuración desde el archivo config.py
mail = Mail(app)  # Inicializa la extensión Mail

#Generar usernames unicos

def generar_username(nombre, apellido_paterno, apellido_materno):
    # Convertir las partes a minúsculas
    nombre_lower = nombre.lower()
    apellido_paterno_lower = apellido_paterno.lower()
    apellido_materno_lower = apellido_materno.lower()

    # Generar el nombre de usuario a partir de las partes
    username = f'{nombre_lower}.{apellido_paterno_lower}{apellido_materno_lower}'
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Verificar si el nombre de usuario ya existe en la base de datos
    query = "SELECT COUNT(*) FROM Usuario WHERE username = %s"
    cursor.execute(query, (username,))
    count = cursor.fetchone()[0]

    # Si el nombre de usuario existe, agregar un número incremental al final
    if count > 0:
        username_base = username
        num = 1
        while True:
            username = f'{username_base}{num}'
            query = "SELECT COUNT(*) FROM Usuario WHERE username = %s"
            cursor.execute(query, (username,))
            count = cursor.fetchone()[0]
            if count == 0:
                break
            num += 1

    return username
    #Genera password random
def generate_random_password(length=8):
    """Genera una contraseña aleatoria de longitud dada."""
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password
    
     # Genera un título único utilizando el módulo uuid
def generar_titulo_unico():
    return str(uuid.uuid4())


# Registro de usuarios
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    password = data['pass']
    nombre = data['name']
    apellido_p = data['apellido_P']
    apellido_m = data['apellido_M']
    email = data['email']
    username = generar_username(nombre,apellido_p,apellido_m)
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    insert_query = "INSERT INTO Usuario (id_Usuario,username, nombre, apellido_P, apellido_M, email, password) VALUES (UUID_TO_BIN(UUID()), %s, %s, %s, %s, %s,%s)"
    cursor.execute(insert_query, (username, nombre, apellido_p, apellido_m, email, password))
    conn.commit()
    cursor.close()
    conn.close()
    # Enviar el correo de confirmación
    message = Message("Registro exitoso", sender=app.config['MAIL_USERNAME'], recipients=[email])
    message.body = f"¡Hola! Gracias por registrarte en nuestra plataforma. Tu nuevo usuario para acceder es {username}"
    mail.send(message)


    return jsonify({'message': 'Registro exitoso'})


# Inicio de sesión
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    select_query = "SELECT * FROM Usuario WHERE username = %s AND password = %s"
    cursor.execute(select_query, (username, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        # Autenticación exitosa
        # Retornar algún token de autenticación si es necesario
        return jsonify({'success': True,'user':username, 'token': 'your_token_here'})
    else:
        # Autenticación fallida
        return jsonify({'success': False, 'message': 'Invalid username or password'})
#Contsena olvidada
@app.route("/password", methods=["POST"])
def reset_password():
    # Consulta la base de datos para verificar si el correo existe
    query = "SELECT * FROM Usuario WHERE email = %s"
    cursor.execute(query, (email,))
    result = cursor.fetchone()

    if result:
        # El correo existe en la base de datos
        # Genera una nueva contraseña aleatoria
        new_password = generate_random_password()

        # Hashea la contraseña utilizando bcrypt
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        # Actualiza la contraseña en la base de datos
        update_query = "UPDATE users SET password = %s WHERE email = %s"
        cursor.execute(update_query, (hashed_password, email))

        # Confirma los cambios en la base de datos
        db.commit()

        # Crea el mensaje de correo
        message = Message("Recuperación de contraseña", sender=app.config['MAIL_USERNAME'], recipients=[email])
        message.body = f"Hola, tu nueva contraseña es: {new_password}"

        # Envía el correo
        mail.send(message)

        return jsonify({"success": True, "message": "Email sent"})
    else:
        # El correo no existe en la base de datos
        return jsonify({"success": False, "message": "Email not found"})




#Subir audio al servidor
@app.route('/upload', methods=['POST'])
def upload():
    if 'audio' not in request.files:
        return 'No se proporcionó ningún archivo de audio', 400
    
    audio_get = request.files['audio']
    username = request.form['username']  # Obtener el nombre de usuario del parámetro
    audio_get.seek(0)  # Vuelve al principio del archivo
    titulo = generar_titulo_unico()  # Genera un título único
    
    # Cargar el archivo de audio
    audio_data_blob = BytesIO(audio_get.read())
    audio_get.seek(0)
    audio_database=audio_get.read()
    audio, sr = librosa.load(audio_data_blob,sr=44100)
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
        # Guardar el archivo de audio sdrom con reduccion de ruido
        #sf.write('audio_completo.wav', audio_completo, sr, subtype='PCM_16')
        
    elif duracion_actual > 5:
        # Reducir la duración del audio a 5 segundos
        duracion_objetivo = 5

        # Calcular el número de muestras necesarias para obtener la duración objetivo
        muestras_objetivo = int(duracion_objetivo * sr)

        # Recortar el audio para obtener la duración objetivo
        audio_completo = audio[:muestras_objetivo]

        # Guardar el archivo de audio sdrom con reducción de ruido
        #sf.write('audio_reducido.wav', audio_completo, sr, subtype='PCM_16')
    else:
        audio_completo=audio
    
    # Calcular el tamaño de la ventana y la cantidad de muestras de "padding"
    window_size = 5
    alpha=4
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
    
    # Guardar el archivo de audio sdrom con reduccion de ruido
    #sf.write('audio_sdrom.wav', audio_sdrom, sr, subtype='PCM_16')
    
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
    
    # Guardar el archivo de audio sdrom con reduccion de ruido
    #sf.write('filtropa.wav', y_cut, sr, subtype='PCM_16')

    # Obtener los coeficientes MFCC del archivo de audio
    mfcc = librosa.feature.mfcc(y=y_cut, sr=sr, n_fft=2048,n_mels=40)

    features = np.mean(mfcc.T, axis=0)
    
    print(features)
    # Guarda los features en un archivo CSV
    df = pd.DataFrame(features.reshape((1, 20)))  # Convierte los features en un DataFrame 
    
    #Debemos convertirlo a un matriz de None,20
    df.to_csv(titulo+'.csv', index=False)  # Guarda el DataFrame en un archivo CS
    
    new_data = pd.read_csv(titulo+'.csv')
    
    # Elimina el archivo CSV
    file_path = titulo+'.csv'  # Ruta del archivo CSV
    if os.path.exists(file_path):  # Verifica si el archivo existe
        os.remove(file_path)  # Elimina el archivo
        print("Archivo CSV eliminado:", file_path)
    else:
        print("El archivo CSV no existe:", file_path)

    model = tf.keras.models.load_model('rednc.h5')

    predictions = model.predict(new_data)
    predicted_classes = np.argmax(predictions, axis=1)

    
    for prediction in predicted_classes:
        if prediction == 1:
            print("Clase predicha: hambre")
            clasificacion="Hambre"
        elif prediction == 2:
            print("Clase predicha: descontento")
            clasificacion="Descontento"
        else:
            print("Clase predicha desconocida")
            clasificacion="Desconocido"
        
    print("Predicciones:", predicted_classes)

    label_names = ['1', '2']  # Reemplaza con los nombres de tus clases

    predicted_labels = [label_names[prediction] for prediction in predicted_classes]
    print("Clases predichas:", predicted_labels)
    
    try:
        # Establece la conexión a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Obtén el id_Usuario desde la tabla Usuario
        cursor.execute('SELECT id_Usuario FROM Usuario WHERE username="'+username+'"')
        id_usuario = cursor.fetchone()[0]  # Suponiendo que solo necesitas el primer resultado
        
        # Inserta los datos en la tabla Audio
        sql = "INSERT INTO Audio (id_Audio, titulo, tam, audio, fecha, clasificacion, id_Usuario) VALUES (UUID_TO_BIN(UUID()), %s, %s, %s, NOW(), %s, %s)"
        cursor.execute(sql, (titulo, duracion_actual, audio_data_blob.getvalue() , clasificacion, id_usuario))
        
        # Guarda los cambios en la base de datos
        conn.commit()

        # Cierra la conexión
        cursor.close()
        conn.close()
        
        # Devuelve la clasificación en formato JSON
        response = {
        'id_audio': titulo,
        'clasificacion': clasificacion
        }

        return json.dumps(response), 200

    except mysql.connector.Error as error:
        return 'Error al guardar el archivo de audio en la base de datos: {}'.format(error), 500

# Ruta de la API para obtener los audios de un usuario
@app.route('/audios', methods=['POST'])
def get_audios():

    username=request.json.get("username")
    try:
        # Conexión a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Consulta SQL para obtener los audios del usuario
        query = 'SELECT a.titulo, a.clasificacion, a.fecha, BIN_TO_UUID(a.id_Audio) , u.username FROM Audio a INNER JOIN Usuario u ON a.id_Usuario = u.id_Usuario WHERE u.username='+username
        
        # Ejecutar la consulta
        cursor.execute(query)
        result = cursor.fetchall()
       
        # Crear una lista de diccionarios con los datos de los audios
        audios = []
        for row in result:
            audio = {
                'titulo': row[0],
                'clasificacion': row[1],
                'fecha': row[2].strftime('%Y-%m-%d %H:%M:%S'),  # Convertir fecha a formato string
                'id_Audio': row[3]
            }
            audios.append(audio)

        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()

        # Devolver la lista de audios en formato JSON
        return jsonify(audios)
    
    except mysql.connector.Error as error:
        # Manejo de errores
        print(f'Error al obtener los audios: {error}')
        return jsonify({'error': 'Ocurrió un error al obtener los audios'}), 500

# Ruta de la API para obtener los audios de un usuario
@app.route('/get_audios', methods=['POST'])
def get_audios_download():
    username=request.json.get("username")
    print(username)
    try:
        # Conexión a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Consulta SQL para obtener los audios del usuario
        query = 'SELECT a.titulo, a.tam, BIN_TO_UUID(a.id_Audio), u.username FROM Audio a INNER JOIN Usuario u ON a.id_Usuario = u.id_Usuario WHERE u.username='+username
        # Ejecutar la consulta
        cursor.execute(query)
        result = cursor.fetchall()
        # Crear una lista de diccionarios con los datos de los audios
        audios = []
        for row in result:
            audio = {
                'titulo': row[0],
                'tam': row[1],
                'id_Audio': row[2]
            }
            audios.append(audio)

        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()

        # Devolver la lista de audios en formato JSON
        return jsonify(audios)
    
    except mysql.connector.Error as error:
        # Manejo de errores
        print(f'Error al obtener los audios: {error}')
        return jsonify({'error': 'Ocurrió un error al obtener los audios'}), 500

@app.route('/download_audio', methods=['POST'])
def download_audio():
    archivo_id = request.json.get('archivoId')

    try:
        # Conexión a la base de datos y consulta para obtener el archivo de audio
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "SELECT audio, titulo FROM Audio WHERE id_Audio = UUID_TO_BIN(%s)"
        cursor.execute(query, (archivo_id,))
        result = cursor.fetchone()
         # Verificar si se encontró el archivo de audio
        if result is None:
            return jsonify({'error': 'Archivo no encontrado'}), 404
        
        audio_blob = result[0]
        titulo = result[1]
        
        # Crear un objeto BytesIO a partir del BLOB de audio
        audio_data_blob = BytesIO(audio_blob)
        audio_server, sr_server = sf.read(audio_data_blob)  
        
        # Crear un archivo temporal para almacenar el audio
        audio_file_path = './'+titulo+'.wav'
        
        # Guardar el archivo de audio sdrom con reducción de ruido
        sf.write(audio_file_path, audio_server, sr_server, subtype='PCM_16')
        
        # Crear una respuesta con el audio
        response = make_response(audio_blob)
    
        # Enviar el archivo de audio como respuesta al cliente
        response = send_file(audio_file_path, mimetype='audio/wav')
        response.headers['Content-Disposition'] = f'attachment; filename={audio_file_path}'
        #response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        # Eliminar el archivo temporal
        os.remove(audio_file_path)
        
        return response
    except mysql.connector.Error as error:
        # Manejo de errores
        print(f'Error al descargar el archivo de audio: {error}')
        return jsonify({'error': 'Ocurrió un error al descargar el archivo de audio'}), 500

@app.route('/informacion-personal', methods=["POST"])
def obtener_informacion_personal():
    username = request.json.get('username')
    try:
    
        
        # Conexión a la base de datos y consulta para obtener la información personal del usuario
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = 'SELECT nombre, apellido_P, apellido_M, email FROM Usuario WHERE username ='+username
        cursor.execute(query)
        result = cursor.fetchone()
        
        # Verificar si se encontró la información personal del usuario
        if result is None:
            return jsonify({'error': 'Información personal no encontrada'}), 404
        
        informacion_personal = {
            'nombre': result[0],
            'apellido_P': result[1],
            'apellido_M': result[2],
            'email': result[3]
        }
        
        return jsonify(informacion_personal)
    
    except mysql.connector.Error as error:
        # Manejo de errores
        print(f'Error al obtener la información personal: {error}')
        return jsonify({'error': 'Ocurrió un error al obtener la información personal'}), 500



if __name__ == '__main__':
    app.run(host="0.0.0.0",port='5000')
