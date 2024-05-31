# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()

db = SQLAlchemy()


# Login models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

# Admin models

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    pathologies = db.relationship('Pathology', secondary='pathology_test', back_populates='tests')
    test_prices = db.relationship('PathologyTestPrice', back_populates='test')

class Pathology(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    area = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    password = db.Column(db.String(60), nullable=False)
    tests = db.relationship('Test', secondary='pathology_test', back_populates='pathologies')
    test_prices = db.relationship('PathologyTestPrice', back_populates='pathology')
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

class PathologyTestPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pathology_id = db.Column(db.Integer, db.ForeignKey('pathology.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    pathology = db.relationship('Pathology', back_populates='test_prices')
    test = db.relationship('Test', back_populates='test_prices')


# Association table for the many-to-many relationship between Pathology and Test
pathology_test = db.Table('pathology_test',
    db.Column('pathology_id', db.Integer, db.ForeignKey('pathology.id'), primary_key=True),
    db.Column('test_id', db.Integer, db.ForeignKey('test.id'), primary_key=True)
)


class PathologyPatient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pathology_id = db.Column(db.Integer, db.ForeignKey('pathology.id'), nullable=False)
    test_name = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    date = db.Column(db.Date, nullable=False)
    slot = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending', nullable=False)

    pathology = db.relationship('Pathology', back_populates='patients')

# Add this relationship to the Pathology model
Pathology.patients = db.relationship('PathologyPatient', back_populates='pathology')

def init_app(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
