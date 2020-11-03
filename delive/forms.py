import re

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, InputRequired, regexp, Email

TEL_REG = r'^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$'


def password_check(form, field):
    msg = "Пароль должен содержать латинские сивмолы в верхнем и нижнем регистре и цифры"
    patern1 = re.compile('[a-z]+')
    patern2 = re.compile('[A-Z]+')
    patern3 = re.compile('\d+')
    if (not patern1.search(field.data) or
            not patern2.search(field.data) or
            not patern3.search(field.data)):
        raise ValidationError(msg)


class LoginForm(FlaskForm):
    username = StringField("Электронная почта:",
                           validators=[DataRequired(), Email(message="Некорректный адрес электронной почты")])
    password = PasswordField("Пароль:", validators=[DataRequired()])


class RegistrationForm(FlaskForm):
    username = StringField(
        "Электронная почта:",
        validators=[
            DataRequired(),
            Email(message="Некорректный адрес электронной почты")
        ]
    )
    password = PasswordField(
        "Пароль:",
        validators=[
            DataRequired(),
            Length(min=8, message="Пароль должен быть не менее 8 символов"),
            EqualTo('confirm_password', message="Пароли не одинаковые"),
            password_check
        ]
    )
    confirm_password = PasswordField("Пароль ещё раз:", validators=[DataRequired()])


class ChangePasswordForm(FlaskForm):
    password = PasswordField(
        "Пароль:",
        validators=[
            DataRequired(),
            Length(min=8, message="Пароль должен быть не менее 8 символов"),
            EqualTo('confirm_password', message="Пароли не одинаковые"),
            password_check
        ]
    )
    confirm_password = PasswordField("Пароль ещё раз:", validators=[DataRequired()])


class OrderForm(FlaskForm):
    clientName = StringField(
        "Ваше имя: ",
        validators=[
            DataRequired(message="Необходимо ввести имя"),
            Length(min=4, max=32, message="Имя должно быть не менее 3 и не боле 32 символов"),
        ]
    )
    
    clientAdress = StringField(
        "Адрес доставки: ",
        validators=[
            DataRequired(message="Необходимо ввести адрес"),
            Length(min=10, max=100, message="Адрес должен иметь не менее 10 и не боле 100 символов"),
        ]
    )
    clientEmail = StringField("Ваш электронный адрес: ",
                              validators=[InputRequired(message="Необходимо ввести электронный адрес"),
                                          Email(message="Некорректный адрес электронной почты")])
    
    clientPhone = StringField("Ваш телефон: ", validators=[InputRequired(message="Необходимо ввести телефон"),
                                                           regexp(TEL_REG,
                                                                  message="Телефон должен содержать от 6 до 11 цифр")])
