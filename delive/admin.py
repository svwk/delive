from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from wtforms.validators import DataRequired, Email, Length
from flask_admin.form import SecureForm

from delive import User, Order, Dish, app, db, Category, session, abort


class MyModelView(ModelView):
    page_size = 50  # the number of entries to display on the list view
    can_view_details = True
    can_export = True
    form_base_class = SecureForm
    
    def is_accessible(self):
        if session.get("user", None):
            user = session["user"]
            if user["role"] == 0:
                return True
        return False
    
    def is_visible(self):
        return self.is_accessible()
    
    def inaccessible_callback(self, name, **kwargs):
        abort(403, description="Вам сюда нельзя")


class MyMenuLink(MenuLink):
    def is_accessible(self):
        if session.get("user", None):
            user = session["user"]
            if user["role"] == 0:
                return True
        return False
    
    def is_visible(self):
        return self.is_accessible()
    
    def inaccessible_callback(self, name, **kwargs):
        abort(403, description="Вам сюда нельзя")


class UserModelView(MyModelView):
    column_exclude_list = ['password_hash', ]
    form_excluded_columns = ['password_hash', ]
    column_searchable_list = ['role']
    column_editable_list = ['role', 'email']
    form_choices = {
        'role': [
            (0, 'Админ'),
            (1, 'Пользователь'),
        ]
    }
    column_labels = dict(password_hash='Пароль', role='Роль')
    form_args = {
        'email': {
            'label': 'email',
            'validators': [DataRequired(), Email(message="Некорректный адрес электронной почты")]
        },
        'role': {
            'label': 'Роль',
            'validators': [DataRequired(message="Необходимо указать роль пользователя")]
        },
        'orders': {
            'label': 'Заказы',
        },
    }


class OrderModelView(MyModelView):
    column_exclude_list = ['delivery_address', 'user']
    column_filters = ['name', 'status']
    column_editable_list = ['status', 'phone']
    column_labels = dict(name='Имя', total='Сумма', created='Создан', status='Статус', phone='Телефон',
                         delivery_adress='Адрес', user='Пользователь', dishes='Блюда')
    form_choices = {
        'status': [
            (0, 'accepted'),
            (1, 'is being prepared'),
            (2, 'is shipped'),
            (3, 'is delivered')
        ]
    }
    
    form_args = {
        'name': {
            'label': 'Имя',
            'validators': [DataRequired(message="Необходимо ввести имя"),
                           Length(min=4, max=32, message="Имя должно быть не менее 3 и не боле 32 символов")]
        },
        
        'total': {
            'label': 'Сумма',
            'validators': [DataRequired(message="Необходимо ввести сумму")]
        },
        
        'created': {
            'label': 'Создан',
            'validators': [DataRequired(message="Необходимо ввести дату")]
        },
        
        'status': {
            'label': 'Статус',
            'validators': [DataRequired(message="Необходимо ввести статус")]
        },
        
        'phone': {
            'label': 'Телефон',
            'validators': [DataRequired(message="Необходимо ввести телефон")]
        },
        
        'email': {
            'label': 'email',
            'validators': [DataRequired(message="Необходимо ввести электронный адрес"),
                           Email(message="Некорректный адрес электронной почты")]
        },
        
        'delivery_address': {
            'label': 'Адрес',
            'validators': [DataRequired(message="Необходимо ввести адрес"),
                           Length(min=10, max=100, message="Адрес должен иметь не менее 10 и не боле 100 символов")]
        },
        
        'user': {
            'label': 'Пользователь',
            'validators': [DataRequired(message="Необходимо указать пользователя")]
        },
        
        'dishes': {
            'label': 'Блюда',
            'validators': [DataRequired(message="Выберите одно или несколько блюд")]
        },
        
    }


class DishModelView(MyModelView):
    column_exclude_list = ['picture', 'description']
    column_searchable_list = ['title']
    column_filters = ['category']
    column_editable_list = ['title', 'price', 'category']
    column_labels = dict(title='Название', price='Цена', description='Описание', picture='Изображение',
                         category='Категория',
                         orders='Заказы')
    # inline_models = ['Category']
    form_args = {
        'title': {
            'label': 'Название',
            'validators': [DataRequired(message="Необходимо ввести название блюда")]
        },
        'price': {
            'label': 'Цена',
        },
        'description': {
            'label': 'Описание',
        },
        'picture': {
            'label': 'Изображение',
            'validators': [DataRequired(message="Необходимо указать название файла с изображением блюда")]
        },
        'category': {
            'label': 'Категория',
            'validators': [DataRequired(message="Необходимо указать категорию блюда")]
        },
        'orders': {
            'label': 'Заказы',
        },
    }
    form_widget_args = {
        'description': {
            'rows': 10,
        }
    }


class CategoryModelView(MyModelView):
    column_editable_list = ['title']
    column_labels = dict(title='Название', dishes='Блюда')
    
    form_args = {
        'title': {
            'label': 'Название',
            'validators': [DataRequired(message="Необходимо ввести название категории")]
        },
        'dishes': {
            'label': 'Блюда',
        },
    }


admin = Admin(app, "Панель управления", "/sadmin/")

admin.add_view(UserModelView(User, db.session, "Пользователи", "Магазин"))
admin.add_view(OrderModelView(Order, db.session, "Заказы", "Магазин"))
admin.add_view(DishModelView(Dish, db.session, "Товары", "Магазин"))
admin.add_view(CategoryModelView(Category, db.session, "Категории", "Магазин"))

admin.add_menu_item(MyMenuLink("Перейти на сайт", "/"), "Управление")
admin.add_menu_item(MyMenuLink("Войти в аккаунт", "/account/"), "Управление")
admin.add_menu_item(MyMenuLink("Вход/выход", "/logout"), "Управление")

admin.add_menu_item(MyMenuLink("Создать/обновить БД", "/upgradedb/gdrgr/"), "База данных")
admin.add_menu_item(MyMenuLink("Загрузить данные в чистую БД", "/loaddb/"), "База данных")
