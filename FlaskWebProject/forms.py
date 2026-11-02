from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=64)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=150)])
    author = StringField("Author", validators=[DataRequired(), Length(max=75)])
    body = TextAreaField("Body", validators=[DataRequired(), Length(max=800)])
    image_path = FileField(
        "Image",
        validators=[FileAllowed(["jpg", "jpeg", "png"], "Only JPG and PNG images are allowed.")],
    )
    submit = SubmitField("Save")
