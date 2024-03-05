from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import cv2
import pytesseract
import qrcode
from io import BytesIO
import numpy as np
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://usuario:contrase�a@localhost/nombre_base_de_datos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'tu_clave_secreta'

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
    # Agrega m�s l�neas para extraer otros datos como fecha de nacimiento, lugar de nacimiento, etc.
    return datos_extraidos

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        imagen_acta = request.files['imagen_acta']

        # Leer la imagen del acta de nacimiento y extraer informaci�n con OCR
        img = cv2.imdecode(np.frombuffer(imagen_acta.read(), np.uint8), cv2.IMREAD_COLOR)
        texto = pytesseract.image_to_string(img, lang='spa')

        # Procesar el texto extra�do para identificar los diferentes datos
        datos_extraidos = procesar_texto(texto)

        nuevo_usuario = Usuario(nombre=nombre, apellido=apellido)
        if 'fecha_nacimiento' in datos_extraidos:
            nuevo_usuario.fecha_nacimiento = datos_extraidos['fecha_nacimiento']
        if 'lugar_nacimiento' in datos_extraidos:
            nuevo_usuario.lugar_nacimiento = datos_extraidos['lugar_nacimiento']

        db.session.add(nuevo_usuario)
        db.session.commit()

        # Almacenar la imagen del acta de nacimiento en la base de datos
        nueva_acta = ActaNacimiento(usuario_id=nuevo_usuario.id, imagen_acta=imagen_acta.read())
        db.session.add(nueva_acta)
        db.session.commit()

        return jsonify({'mensaje': 'Usuario registrado exitosamente'}), 201

    return render_template('registro.html')

if __name__ == '__main__':
    app.run(debug=True)
