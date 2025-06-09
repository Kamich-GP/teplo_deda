import sqlite3

# Подключение к БД
connection = sqlite3.connect('delivery.db', check_same_thread=False)
# Python + SQL
sql = connection.cursor()

# Создание таблиц (юзеры, продукты, корзина)
sql.execute('CREATE TABLE IF NOT EXISTS users (tg_id INTEGER, name TEXT, number TEXT);')
sql.execute('CREATE TABLE IF NOT EXISTS products (pr_id INTEGER PRIMARY KEY AUTOINCREMENT, '
            'pr_name TEXT, pr_des TEXT, pr_count INTEGER, pr_price REAL, pr_photo TEXT);')
sql.execute('CREATE TABLE IF NOT EXISTS cart (tg_id INTEGER, '
            'user_product TEXT, user_pr_amount INTEGER);')


## Методы юзера ##
# Регистрация
def register(tg_id, name, number):
    sql.execute('INSERT INTO users VALUES (?, ?, ?);', (tg_id, name, number))
    # Фиксируем изменения
    connection.commit()


# Проверка на наличие юзера в БД
def check_user(tg_id):
    if sql.execute('SELECT * FROM users WHERE tg_id=?;', (tg_id,)).fetchone():
        return True
    else:
        return False


## Методы товаров ##
# Вывод всех товаров
def get_all_pr():
    return sql.execute('SELECT * FROM products;').fetchall()


# Вывод товаров на кнопки
def get_pr_buttons():
    all_products = get_all_pr()
    in_stock = [n[:2] for n in all_products if n[3] > 0]

    return in_stock


# Вывод конкретного товара
def get_exact_pr(pr_id):
    return sql.execute('SELECT * FROM '
                       'products WHERE pr_id=?;', (pr_id,)).fetchone()


# Вывод цены конкретного товара
def get_exact_price(pr_name):
    return sql.execute('SELECT pr_price FROM '
                       'products WHERE pr_name=?;', (pr_name,)).fetchone()[0]


## Корзина ##
# Добавление товара в корзину
def add_to_cart(tg_id, user_product, user_pr_amount):
    sql.execute('INSERT INTO cart VALUES (?, ?, ?);',
                (tg_id, user_product, user_pr_amount))
    # Фиксируем изменения
    connection.commit()


# Очистка корзины
def clear_cart(tg_id):
    sql.execute('DELETE FROM cart WHERE tg_id=?;', (tg_id,))
    # Фиксируем изменения
    connection.commit()


# Отображение корзины
def show_cart(tg_id):
    return sql.execute('SELECT * FROM cart WHERE tg_id=?;', (tg_id,)).fetchall()


# Оформление заказа
def make_order(tg_id):
    # Достаем кол-во товаров, которые взял юзер
    product_names = sql.execute('SELECT user_product FROM cart WHERE tg_id=?;',
                                (tg_id,)).fetchall()
    product_counts = sql.execute('SELECT user_pr_amount FROM cart WHERE tg_id=?;',
                                 (tg_id,)).fetchall()

    # Достаем кол-во товара на СКЛАДЕ
    stock = [sql.execute('SELECT pr_count FROM products '
                         'WHERE pr_name=?;', (i[0],)).fetchone()[0]
             for i in product_names]

    totals = []

    for t in range(len(product_counts)):
        totals.append(stock[t] - product_counts[t][0])

    for c in range(len(totals)):
        sql.execute('UPDATE products SET pr_count=? WHERE pr_name=?;',
                    (totals[c], product_names[c][0]))

    # Фиксируем изменения
    connection.commit()
    return stock, totals



## Админ-панель ##
# Добавление товара в БД
def add_pr_to_db(pr_name, pr_des, pr_count, pr_price, pr_photo):
    if (pr_name,) in sql.execute('SELECT pr_name FROM products;') or int(pr_count) < 1:
        return False
    else:
        sql.execute('INSERT INTO products '
                    '(pr_name, pr_des, pr_count, pr_price, pr_photo) VALUES '
                    '(?, ?, ?, ?, ?);',
                    (pr_name, pr_des, pr_count, pr_price, pr_photo))
        # Фиксируем изменения
        connection.commit()
