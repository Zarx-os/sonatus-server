import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000/'], methods=['GET', 'POST'], allow_headers=['Content-Type'])

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'G@d1266090',
    'database': 'sonatus'
}


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
    query = "SELECT COUNT(*) FROM Usuarios WHERE username = %s"
    cursor.execute(query, (username,))
    count = cursor.fetchone()[0]

    # Si el nombre de usuario existe, agregar un número incremental al final
    if count > 0:
        username_base = username
        num = 1
        while True:
            username = f'{username_base}{num}'
            query = "SELECT COUNT(*) FROM Usuarios WHERE username = %s"
            cursor.execute(query, (username,))
            count = cursor.fetchone()[0]
            if count == 0:
                break
            num += 1

    return username
    
    
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
    insert_query = "INSERT INTO Usuario (id_Usuario,username, nombre, apellido_P, apellido_M, email, password) VALUES (%s, %s, %s, %s, %s, %s,%s)"
    cursor.execute(insert_query, ("UUID_TO_BIN(UUID())",username, nombre, apellido_p, apellido_m, email, password))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Registro exitoso'})


# Inicio de sesión
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    
    print(username)
    print(password)
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

#Subir audio al servidor
@app.route('/upload', methods=['POST'])
def upload():
    if 'audio' not in request.files:
        return 'No se proporcionó ningún archivo de audio', 400
    
    audio = request.files['audio']
    username = request.form.get("username")  # Obtener el nombre de usuario del parámetro
    tam = len(audio.read())  # Obtén el tamaño del archivo de audio
    titulo = generar_titulo_unico()  # Genera un título único
    clasificacion="prueba"
    print(username)
    try:
        # Establece la conexión a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Obtén el id_Usuario desde la tabla Usuario
        cursor.execute('SELECT id_Usuario FROM Usuario WHERE username="'+username+'"')
        id_usuario = cursor.fetchone()[0]  # Suponiendo que solo necesitas el primer resultado
        
        # Inserta los datos en la tabla Audio
        sql = "INSERT INTO Audio (id_Audio, titulo, tam, audio, fecha, clasificacion, id_Usuario) VALUES (UUID_TO_BIN(UUID()), %s, %s, %s, NOW(), %s, %s)"
        cursor.execute(sql, (titulo, tam, audio.read(), clasificacion, id_usuario))

        # Guarda los cambios en la base de datos
        conn.commit()

        # Cierra la conexión
        cursor.close()
        conn.close()

        return 'Archivo de audio recibido y guardado correctamente'

    except mysql.connector.Error as error:
        return 'Error al guardar el archivo de audio en la base de datos: {}'.format(error), 500

if __name__ == '__main__':
    app.run(debug=True)
