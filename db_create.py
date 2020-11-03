from delive import db, config, Dish, Category
db.drop_all()
db.create_all()

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