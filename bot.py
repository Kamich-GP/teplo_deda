import telebot
import database
import buttons


# Создаем объект бота
bot = telebot.TeleBot('TOKEN')
# Создаем хранилище временных данных
users = {}

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    if database.check_user(user_id):
        products = database.get_pr_buttons()
        bot.send_message(user_id, 'Добро пожаловать!',
                         reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.send_message(user_id, 'Выберите пункт меню:',
                         reply_markup=buttons.main_menu(products))
    else:
        bot.send_message(user_id, 'Приветствую! Давайте начнем регистрацию, '
                                  'введите свое имя!',
                         reply_markup=telebot.types.ReplyKeyboardRemove())
        # Переход на этап получения имени
        bot.register_next_step_handler(message, get_name)


# Этап получения имени
def get_name(message):
    user_id = message.from_user.id
    user_name = message.text

    bot.send_message(user_id, 'Отлично! Теперь свой номер телефона!',
                     reply_markup=buttons.num_button())
    # Переход на этап получения номера
    bot.register_next_step_handler(message, get_num, user_name)


# Этап получения номера
def get_num(message, user_name):
    user_id = message.from_user.id

    # Если юзер отправил номер по кнопке
    if message.contact:
        print(message.contact)
        user_num = message.contact.phone_number
        # Регистрируем юзера
        database.register(user_id, user_name, user_num)
        bot.send_message(user_id, 'Регистрация прошла успешно!',
                         reply_markup=telebot.types.ReplyKeyboardRemove())
    # Если юзер отправил номер не по кнопке
    else:
        bot.send_message(user_id, 'Отправьте номер через кнопку!')
        # Возврат на этап получения номера
        bot.register_next_step_handler(message, get_num, user_name)


# Обработка выбора количества товара
@bot.callback_query_handler(lambda call: call.data in ['decrement', 'increment', 'to_cart', 'back'])
def choose_count(call):
    user_id = call.message.chat.id

    if call.data == 'increment':
        bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id,
                                      reply_markup=buttons.choose_pr_count(
                                          database.get_exact_pr(
                                          users[user_id]['pr_name'])[3],
                                          'increment',
                                          users[user_id]['pr_count']))
        users[user_id]['pr_count'] += 1
    elif call.data == 'decrement':
        bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id,
                                      reply_markup=buttons.choose_pr_count(
                                          database.get_exact_pr(
                                          users[user_id]['pr_name'])[3],
                                          'decrement',
                                          users[user_id]['pr_count']))
        users[user_id]['pr_count'] -= 1
    elif call.data == 'to_cart':
        bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
        pr_name = database.get_exact_pr(users[user_id]['pr_name'])[1]
        database.add_to_cart(user_id, pr_name, users[user_id]['pr_count'])
        bot.send_message(user_id, 'Товар успешно помещен в корзину!')
        bot.send_message(user_id, 'Выберите пункт меню:',
                         reply_markup=buttons.main_menu(database.get_pr_buttons()))
    elif call.data == 'back':
        bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
        bot.send_message(user_id, 'Выберите пункт меню:',
                         reply_markup=buttons.main_menu(database.get_pr_buttons()))


# Обработка работы корзины
@bot.callback_query_handler(lambda call: call.data in ['cart', 'clear', 'order'])
def cart_handle(call):
    user_id = call.message.chat.id
    text = 'Ваша корзина:\n\n'

    if call.data == 'cart':
        user_cart = database.show_cart(user_id)
        total = 0.0

        for i in user_cart:
            text += (f'Товар: {i[1]}\n'
                     f'Количество: {i[2]}\n'
                     f'------------------------\n')
            total += database.get_exact_price(i[1]) * i[2]
        text += f'Итого: {round(total, 2)}'
        bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
        bot.send_message(user_id, text, reply_markup=buttons.cart_buttons())
    elif call.data == 'clear':
        database.clear_cart(user_id)
        bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
        bot.send_message(user_id, 'Выберите пункт меню:',
                         reply_markup=buttons.main_menu(database.get_pr_buttons()))
    elif call.data == 'order':
        text = text.replace('Ваша корзина:', f'Новый заказ!\nКлиент @{call.message.chat.username}\n')
        user_cart = database.show_cart(user_id)
        total = 0.0

        for i in user_cart:
            text += (f'Товар: {i[1]}\n'
                     f'Количество: {i[2]}\n'
                     f'------------------------\n')
            total += database.get_exact_price(i[1]) * i[2]
        text += f'Итого: {round(total, 2)}'
        bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
        bot.send_message(user_id, 'Отправьте локацию, куда доставить ваш заказ!',
                         reply_markup=buttons.loc_button())
        # Переход на этап получения локации
        bot.register_next_step_handler(call.message, get_loc, text)


# Этап получения локации
def get_loc(message, text):
    user_id = message.from_user.id
    # Проверка на правильность отправки локации
    if message.location:
        bot.send_message('ваш_тг_айди', text)
        bot.send_location('ваш_тг_айди', latitude=message.location.latitude,
                          longitude=message.location.longitude)
        database.make_order(user_id)
        database.clear_cart(user_id)
        bot.send_message(user_id, 'Ваш заказ оформлен успешно! Скоро с вами свяжутся!',
                         reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.send_message(user_id, 'Выберите пункт меню:',
                         reply_markup=buttons.main_menu(database.get_pr_buttons()))
    else:
        bot.send_message(user_id, 'Отправьте локацию по кнопке!')
        # Возвращаем на этап получения локации
        bot.register_next_step_handler(message, get_loc, text)


# Обработчик команды /admin
@bot.message_handler(commands=['admin'])
def admin(message):
    admin_id = message.from_user.id
    bot.send_message(admin_id, 'Чтобы добавить товар в базу, введите его в следующей последовательности:\n'
                               'Название, описание, кол-во, цена, фото\n\n'
                               'Пример:\n'
                               'Картошка фри, вкусни, 500, 14000, https://kartoxa.jpg\n\n'
                               '<a href="https://postimages.org/">Сайт</a> для загрузки фото.\n'
                               'Пришлите мне прямую ссылку на фото товара!',
                     parse_mode='HTML')
    bot.register_next_step_handler(message, get_pr)


def get_pr(message):
    admin_id = message.from_user.id
    database.add_pr_to_db(*message.text.split(', ')) #['Картошка фри', 'вкусни', 500, 14000, 'https://kartoxa.jpg']
    bot.send_message(admin_id, 'Товар успешно добавлен!')


# Обработчик callback_data на товар
@bot.callback_query_handler(lambda call: int(call.data) in [i[0] for i in database.get_all_pr()])
def choose_product(call):
    user_id = call.message.chat.id
    pr_info = database.get_exact_pr(int(call.data))
    bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
    bot.send_photo(user_id, photo=pr_info[-1], caption=f'<b>{pr_info[1]}</b>\n\n'
                                                       f'<b>Описание: </b>{pr_info[2]}\n'
                                                       f'<b>Количество: </b>{pr_info[3]}\n'
                                                       f'<b>Цена: </b>{pr_info[4]} сум\n',
                   parse_mode='HTML', reply_markup=buttons.choose_pr_count(pr_info[3]))
    users[user_id] = {'pr_name': pr_info[0], 'pr_count': 1}


# Запуск бота
bot.polling(non_stop=True)
