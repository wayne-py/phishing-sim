from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField, SubmitField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
import datetime
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class EmailTemplateForm(FlaskForm):
    name = StringField('Template Name', validators=[DataRequired(), Length(max=100)])
    subject = StringField('Email Subject', validators=[DataRequired(), Length(max=200)])
    sender_name = StringField('Sender Name', validators=[DataRequired(), Length(max=100)])
    sender_email = StringField('Sender Email', validators=[DataRequired(), Email(), Length(max=120)])
    content = TextAreaField('Email Content (HTML)', validators=[DataRequired()])
    submit = SubmitField('Save Template')

class CampaignForm(FlaskForm):
    name = StringField('Campaign Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    template_id = SelectField('Email Template', coerce=int, validators=[DataRequired()])
    schedule = BooleanField('Schedule for later')
    scheduled_time = DateTimeField('Schedule Date/Time', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    submit = SubmitField('Save Campaign')
    
    def validate_scheduled_time(self, field):
        if self.schedule.data and field.data:
            if field.data < datetime.datetime.now():
                raise ValidationError('Scheduled time must be in the future')

class TargetForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField('Add Target')

class EducationalContentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Main Content', validators=[DataRequired()])
    tips = TextAreaField('Security Tips', validators=[DataRequired()])
    submit = SubmitField('Save Content')