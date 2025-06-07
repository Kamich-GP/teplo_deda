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
