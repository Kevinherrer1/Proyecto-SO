from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Modelo de Usuario
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date)
    lugar_nacimiento = db.Column(db.String(100))
    acta_nacimiento = db.relationship('ActaNacimiento', backref='usuario', uselist=False)

    def __repr__(self):
        return f"<Usuario {self.nombre} {self.apellido}>"

# Modelo de Acta de Nacimiento
class ActaNacimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    numero_acta = db.Column(db.String(20), nullable=False)
    imagen_acta = db.Column(db.LargeBinary, nullable=False)

    def __repr__(self):
        return f"<ActaNacimiento {self.numero_acta}>"
