from datetime import datetime

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
migrate = Migrate()


# Форматирование даты заказа
def showdate():
    value = datetime.now()
    if value:
        day = value.day
        year = value.year
        m = value.month
        month = ["января", "фераля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября",
                 "ноября", "декабря"][m - 1]
        return f"{day} {month} {year} г."
    return ""


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, )
    email = db.Column(db.String(30), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    # role: 0 - admin, 1 - buyer
    role = db.Column(db.Integer, nullable=False)
    
    orders = db.relationship("Order", back_populates='user')
    
    @property
    def password(self):
        raise AttributeError("Вам не нужно знать пароль!")
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def password_valid(self, password):
        return check_password_hash(self.password_hash, password)


dishes_orders = db.Table('dishes_orders',
                         db.Column('dish_id', db.Integer, db.ForeignKey('dishes.id')),
                         db.Column('order_id', db.Integer, db.ForeignKey('orders.id'))
                         )


class Dish(db.Model):
    __tablename__ = 'dishes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(130), nullable=False)
    price = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, nullable=False)
    picture = db.Column(db.String(50), default="")
    
    category_id = db.Column(db.Integer, ForeignKey('categories.id'), nullable=False)
    category = db.relationship("Category", back_populates='dishes')
    orders = db.relationship('Order', secondary=dishes_orders, back_populates='dishes')


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), nullable=False)
    
    dishes = db.relationship("Dish", back_populates='category')


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.String(20), default=showdate())
    name = db.Column(db.String(30), nullable=False)
    total = db.Column(db.Integer, default=0)
    # status: 0 - accepted, 1 - is being prepared, 2 - is shipped, 3 - is delivered
    status = db.Column(db.Integer, default=0)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(30), nullable=False)
    delivery_address = db.Column(db.String(250), nullable=False)
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    user = db.relationship("User", back_populates='orders')
    dishes = db.relationship('Dish', secondary=dishes_orders, back_populates='orders')
