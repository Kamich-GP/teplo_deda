from telebot import types


# Кнопка отправки номера
def num_button():
    # Создание пространства
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Создание самих кнопок
    but1 = types.KeyboardButton('Отправить номер телефона📞', request_contact=True)
    # Добавление кнопок в пространство
    kb.add(but1)

    return kb


# Кнопки главного меню
def main_menu(products):
    # Создание пространства
    kb = types.InlineKeyboardMarkup(row_width=2)
    # Создание самих кнопок
    cart = types.InlineKeyboardButton(text='Корзина🛒',
                                      callback_data='cart')
    all_products = [types.InlineKeyboardButton(text=i[1],
                                               callback_data=i[0])
                    for i in products]
    # Добавление кнопок в пространство
    kb.add(*all_products)
    kb.row(cart)

    return kb
