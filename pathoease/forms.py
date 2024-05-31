# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError, validators
from wtforms.validators import DataRequired, Email, EqualTo
from models import User
from flask import flash

class RegistrationForm(FlaskForm):
    name = StringField('Name:', validators=[DataRequired()])
    email = StringField('Email:', validators=[DataRequired(), Email()])
    password = PasswordField('Password:', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password:', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email is already in use. Please choose a different one.')
    
    def validate_confirm_password(self, field):
        if self.password.data != field.data:
            raise ValidationError('Passwords do not match. Please enter matching passwords.')
        
class LoginForm(FlaskForm):
    email = StringField('Email:', validators=[DataRequired(), Email()])
    password = PasswordField('Password:', validators=[DataRequired()])
    submit = SubmitField('Log In')

class PathologyLoginForm(FlaskForm):
    unique_id = StringField('Unique ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')