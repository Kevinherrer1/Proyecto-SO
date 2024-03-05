from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import cv2
import pytesseract
import numpy as np
import re
import base64
import os
import qrcode

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://usuario:contraseña@localhost/nombre_base_de_datos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'tu_clave_secreta'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['QR_CODES_FOLDER'] = 'qr_codes'

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date)
    lugar_nacimiento = db.Column(db.String(100))

class ActaNacimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    numero_acta = db.Column(db.String(20), nullable=False)
    imagen_acta = db.Column(db.LargeBinary, nullable=False)

db.create_all()

def procesar_texto(texto):
    datos_extraidos = {}
    datos_extraidos['nombre'] = re.search(r'Nombre: (\w+)', texto).group(1)
    datos_extraidos['apellido'] = re.search(r'Apellido: (\w+)', texto).group(1)
    # Agrega más líneas para extraer otros datos como fecha de nacimiento, lugar de nacimiento, etc.
    return datos_extraidos

@app.route('/registro', methods=['POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        foto_base64 = request.form['imagen_acta']

        # Decodificar la imagen de base64
        foto_decodificada = base64.b64decode(foto_base64.split(',')[1])
        # Guardar la imagen en un archivo temporal
        ruta_imagen_temporal = 'temp.jpg'
        with open(ruta_imagen_temporal, 'wb') as f:
            f.write(foto_decodificada)

        # Leer la imagen del acta de nacimiento
        img = cv2.imread(ruta_imagen_temporal)
        # Extraer información con OCR
        texto = pytesseract.image_to_string(img, lang='spa')
        # Procesar el texto extraído
        datos_extraidos = procesar_texto(texto)

        nuevo_usuario = Usuario(nombre=nombre, apellido=apellido)
        if 'fecha_nacimiento' in datos_extraidos:
            nuevo_usuario.fecha_nacimiento = datos_extraidos['fecha_nacimiento']
        if 'lugar_nacimiento' in datos_extraidos:
            nuevo_usuario.lugar_nacimiento = datos_extraidos['lugar_nacimiento']

        db.session.add(nuevo_usuario)
        db.session.commit()

        # Generar y almacenar el código QR asociado al usuario
        qr_code_data = f'User ID: {nuevo_usuario.id}'  # Puedes personalizar los datos que contiene el código QR
        qr_code = qrcode.make(qr_code_data)
        qr_code_path = os.path.join(app.config['QR_CODES_FOLDER'], f'{nuevo_usuario.id}.png')
        qr_code.save(qr_code_path)

        # Almacenar la imagen del acta de nacimiento en la base de datos
        nueva_acta = ActaNacimiento(usuario_id=nuevo_usuario.id, imagen_acta=foto_decodificada)
        db.session.add(nueva_acta)
        db.session.commit()

        # Eliminar el archivo temporal
        os.remove(ruta_imagen_temporal)

        return jsonify({'mensaje': 'Usuario registrado exitosamente', 'qr_code_path': qr_code_path}), 201

    return jsonify({'mensaje': 'Solicitud no válida'}), 400

if __name__ == '__main__':
    app.run(debug=True)
