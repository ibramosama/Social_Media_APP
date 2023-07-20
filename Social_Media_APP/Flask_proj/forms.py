from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, PasswordField, SubmitField, FileField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=255)])
    submit = SubmitField('Log In')

class PostForm(FlaskForm):
    content = StringField('Content', validators=[DataRequired()])
    privacy = SelectField('Privacy', choices=[
        ('Public', 'Public'),
        ('Friends', 'Friends Only'),
        ('Only Me', 'Only Me')
    ], validators=[DataRequired()])

class FriendRequestForm(FlaskForm):
    friend_id = StringField('Friend ID', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Send Friend Request')

class ChatForm(FlaskForm):
    message_content = StringField('Message Content', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Send Message')


class EditProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    profile_picture = FileField('Profile Picture')
    submit = SubmitField('Save Changes')



