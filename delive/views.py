from functools import wraps
import random
from hashlib import md5

import flask_migrate
from flask import abort, flash, session, redirect, request, render_template, url_for
from sqlalchemy.exc import OperationalError, ProgrammingError

from delive import app, db
from delive.models import User, Dish, Order, Category
import delive.forms as forms
import delive.config as config


# Декораторы авторизации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    
    return decorated_function


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user'):
            if session["user"]["role"] == 0:
                return f(*args, **kwargs)
        abort(403, description="Вам сюда нельзя")
    
    return decorated_function


# фильтр для случайного отбора элементов по категории
@app.template_filter('sample')
def sample_filter(items, items_count):
    if items and len(items) > items_count:
        random.seed()
        return random.sample(items, items_count)
    else:
        return items


# Фильтр для форматированного вывода статуса заказа
@app.template_filter('getstatus')
def getstatus_filter(value):
    if type(value) != int:
        value = int(value)
    
    return ["заказ принят", "заказ готовится", "заказ доставляется", "заказ доставлен и вручен"][value]


@app.route('/')
def home():
    # Загрузка данных
    categories = db.session.query(Category).all()
    dishes = db.session.query(Dish).all()
    
    return render_template("main.html", dishes=dishes, categories=categories)


# Страница корзины
@app.route('/cart/', methods=['GET', 'POST'])
def show_cart():
    cart = session.get("cart", [])
    form = forms.OrderForm()
    
    # Если данные не были отправлены или не прошли валидацию
    if request.method != "POST" or not form.validate_on_submit():
        dishes = []
        if cart:
            for c in cart:
                dish = db.session.query(Dish).get(c)
                if dish:
                    dishes.append(dish)
        
        # снова показываем  страницу корзины
        if session.get("user", None):
            form.clientEmail.data = session["user"]["email"]
        
        return render_template("cart.html", dishes=dishes, form=form)
    
    u = session.get("user", None)
    if not u:
        return redirect(url_for('login'))
    
    # Если данные были отправлены
    # получаем данные
    client_name = form.clientName.data
    client_phone = form.clientPhone.data
    client_address = form.clientAdress.data
    client_email = form.clientEmail.data
    
    # сохраняем данные
    try:
        order = Order(name=client_name, phone=client_phone, delivery_address=client_address, email=client_email,
                      total=session.get("total", 0), status=0, user_id=u["id"])
        for dish_id in cart:
            dish = db.session.query(Dish).get(dish_id)
            if dish:
                order.dishes.append(dish)
        
        db.session.add(order)
        db.session.commit()
        
        # Обнуляем данные корзины в сессии
        session["total"] = 0
        session["cart"] = []
        session["count"] = 0
    
    except (OperationalError, ProgrammingError):
        return render_template('error.html', text="К сожалению, на сайте произошла неустранимая ошибка"), 500
    
    # переходим на ordered
    return render_template('ordered.html', clientid=client_name)


# Добавление в корзину
@app.route('/addtocart/<int:dish_id>/')
def render_addtocart(dish_id):
    
    try:
        item = db.session.query(Dish).get(dish_id)
    except (OperationalError, ProgrammingError):
        return render_template('error.html', text="К сожалению, на сайте произошла неустранимая ошибка"), 500
    
    if not item:
        return render_template('error.html', text="К сожалению, данного товара в нашей базе данных нет"), 404
    
    # Получаем либо значение из сессии, либо пустой список
    cart = session.get("cart", [])
    
    # Добавлям элемент в список
    if cart:
        if item.id in cart:
            flash('Вы не можете добавлять в корзину два и более одинаковых товара')
            return redirect("/")
    
    cart.append(item.id)
    
    # Записываем список обратно в сессию
    session['cart'] = cart
    session['total'] = session.get("total", 0) + item.price
    session['count'] = len(cart)
    
    return redirect(url_for("show_cart"))


# Удаление из корзины
@app.route('/delete_dish/<int:dish_id>/')
def delete_dish(dish_id):
    cart = session.get("cart", [])
    
    if cart and dish_id in cart:
        dish = db.session.query(Dish).get(dish_id)
        if dish:
            cart.remove(dish_id)
            total = session.get("total", 0) - dish.price
            count = session.get("total", 0) - 1
            flash(f'Товар {dish.title} удален из корзины')
            
            if total < 0 or count < 0 or not cart:
                session['total'] = 0
                session['cart'] = []
                session['count'] = 0
            else:
                session['total'] = total
                session['cart'] = cart
                session['count'] = count
    
    return redirect(url_for("show_cart"))


# Страница кабинета
@app.route('/account/')
@login_required
def render_account():
    u = session.get("user", None)
    if not u:
        return redirect(url_for('login'))
    
    user = User.query.get(u["id"])
    if user:
        return render_template("account.html", user=user, change_password=False)
    
    flash("Произошла ошибка с вашей учетной записью. Выйдите и войдите снова или пройдите регистрацию")
    return redirect("/")


# Страница админки
@app.route('/admin/')
@admin_only
def render_admin():
    return redirect("/sadmin/")


# Страница аутентификации
@app.route("/login/", methods=["GET", "POST"])
def login():
    # Если пользователь уже вошел, перенаправляем его на страницу кабинета
    if session.get("user"):
        return redirect(url_for('render_account'))
    
    form = forms.LoginForm()
    
    # Если данные были отправлены и прошли валидацию
    if request.method == "POST" and form.validate_on_submit():
        user = User.query.filter_by(email=form.username.data).first()
        if user and user.password_valid(form.password.data):
            session["user"] = {
                "id": user.id,
                "email": user.email,
                "role": user.role,
            }
            # Пользователь вошел, отправляем на главную
            return redirect("/")
        
        # Пользователь не вошел, отправляем снова на страницу аутентификации
        flash("Неправильный логин или пароль")
        form.password.data = ""
    
    return render_template("login.html", form=form)


# Выход из учетной записи
@app.route('/logout/', methods=["GET"])
@login_required
def logout():
    if session.get("user"):
        session.pop("user")
    return redirect(url_for('login'))


# Страница регистрации пользователя
@app.route("/registration/", methods=["GET", "POST"])
def registration():
    # Если пользователь уже вошел, перенаправляем его на страницу кабинета
    if session.get("user"):
        return redirect(url_for('render_account'))
    
    form = forms.RegistrationForm()
    
    # Если данные были отправлены и прошли валидацию
    if request.method == "POST" and form.validate_on_submit():
        user = User.query.filter_by(email=form.username.data).first()
        if not user:
            user = User()
            user.email = form.username.data
            user.password = form.password.data
            user.role = 1
            db.session.add(user)
            db.session.commit()
            
            # Пользователь создан, авторизуем и отправляем на главную
            session["user"] = {
                "id": user.id,
                "email": user.email,
                "role": user.role,
            }
            
            flash(f"Пользователь: {form.username.data} с паролем: {form.password.data} зарегистрирован")
            return redirect("/")
        
        flash("Пользователь с таким именем уже существует")
    
    return render_template("register.html", form=form)


# Страница смены пароля
@app.route("/change-password/", methods=["GET", "POST"])
@login_required
def change_password():
    u = session["user"]["id"]
    
    user = User.query.get(u)
    if not user:
        flash("Произошла ошибка с вашей учетной записью. Выйдите и войдите или снова пройдите регистрацию")
        return redirect("/")
    
    form = forms.ChangePasswordForm()
    
    if request.method == "POST" and form.validate_on_submit():
        # Обновляем пароль у текущего пользователя по его идентификатору
        user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        flash(f"Ваш пароль изменён")
        return redirect(url_for('render_account'))
    
    return render_template("account.html", form=form, change_password=True, user=user)


# апгрейд БД
@app.route('/upgradedb/<page>/')
def upgrade_db(page):
    # если не админ
    if not session.get('user') or session["user"]["role"] != 0:
        # примитивная мера защиты
        if md5(page.encode()).hexdigest() != r'ec7af1e43f5c009460e1f459f143fd25':
            return redirect(url_for('home'))
    
    flask_migrate.upgrade()
    
    # Добавление админа, чтобы можно было войти в админку
    user = User(id=0, email='admin@admin.ru', role=0)
    user.password = 'grW4Vd*fhQXT#5b92JrV'
    db.session.add(user)
    db.session.commit()
    
    # администратор создан, авторизуем и отправляем в кабинет для задания пароля
    session["user"] = {
        "id": user.id,
        "email": 'admin@admin.ru',
        "role": 0,
    }
    flash('Не забудьте задать пароль, чтобы и далее иметь возможность пользоваться учетной записью администратора!')
    
    return redirect(url_for('render_account'))


# Загрузка данных в пустую базу данных
@app.route('/loaddb/')
@admin_only
def load_db():
    # Загрузка данных
    try:
        with open(f'{config.current_path}/data/source_data.csv', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        content = None
    if content:
        lst = content.split('\n')
        if len(lst) > 1:
            for value in lst[1:]:
                items = value.split('|')
                if items and len(items) > 5:
                    dish = Dish(id=int(items[0]), title=items[1], price=int(items[2]), description=items[3],
                                picture=items[4], category_id=int(items[5]))
                    db.session.add(dish)
    
    try:
        with open(f'{config.current_path}/data/category.csv', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        content = None
    
    if content and len(content) > 1:
        lst = content.split('\n')
        if len(lst) > 1:
            for value in lst[1:]:
                items = value.split('|')
                if items and len(items) > 1:
                    cat = Category(id=int(items[0]), title=items[1])
                    db.session.add(cat)
    
    db.session.commit()
    
    return redirect(url_for('home'))


@app.errorhandler(404)
def render_not_found(error):
    return render_template('error.html', text="Ничего не нашлось!"), 404


@app.errorhandler(500)
def render_server_error(error):
    return render_template('error.html',
                           text="Что-то не так, но мы все починим:\n{}".format(error.original_exception)), 500
