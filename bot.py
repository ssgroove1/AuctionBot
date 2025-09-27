from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from logic import *
import schedule
import threading
import time
from config import *

adminisration = 1692557632

bot = TeleBot(API_TOKEN)

def gen_markup(id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Получить!", callback_data=id))
    return markup
    

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):

    prize_id = call.data
    user_id = call.message.chat.id
    if call.data == "cb_first":
        bot.send_message(user_id, 'Отправьте фотографию которую хотите добавить: ')
        bot.register_next_step_handler(call.message, add_image)

    elif call.data == 'cb_second':
        send_message()
        bot.send_message(user_id, 'Вы успешно отправили всем пользователем бонусный приз!')


    elif call.data == 'cb_third':
        manager.mark_prize_update()
        bot.send_message(user_id, 'Вы успешно обновили все призы!')


    elif call.data == "cb_shop1":
        if manager.show_score(user_id) >= 15:
            if manager.sum_used_prize() >= 1:
                prize_id, img = manager.get_random_used_prize()[:2]
                hide_img(img)
                with open(f'hidden_img/{img}', 'rb') as photo:
                    bot.send_photo(user_id, photo, caption="Бонусный приз", reply_markup=gen_markup(id = prize_id))
                manager.remove_score(15, user_id)
            else:
                bot.send_message(user_id, 'Простите, но в данный момент вы не можете использовать эту функцию.')
        else:
            bot.send_message(user_id, 'У вас недостаточно шоколадок.')


    elif call.data == "cb_shop2":
        if manager.show_score(user_id) >= 45:
            if manager.sum_used_prize() >= 1:
                manager.mark_prize_update()
                manager.remove_score(45, user_id)
                bot.send_message(user_id, 'Вы успешно обновили все призы, новые игроки теперь смогут их получить!')
            else:
                bot.send_message(user_id, 'Простите, но в данный момент вы не можете использовать эту функцию.')
        else:
            bot.send_message(user_id, 'У вас недостаточно шоколадок.')


    else:
        if manager.get_winners_count(prize_id) < 3:
            res = manager.add_winner(user_id, prize_id)
            if res:
                img = manager.get_prize_img(prize_id)
                manager.add_score(5, user_id)
                with open(f'img/{img}', 'rb') as photo:
                    bot.send_photo(user_id, photo, caption="Поздравляем! Ты получил картинку и бонус в качестве 5 🍫!")
            else:
                bot.send_message(user_id, 'Ты уже получил картинку!')
        else:
            bot.send_message(user_id, "К сожалению, ты не успел получить картинку! Попробуй в следующий раз!)")


def add_image(message):
    # Получаем информацию о фотографии  
    photo = message.photo[-1]  
    file_id = photo.file_id  
    file_info = bot.get_file(file_id)  
    # Загружаем фотографию на локальный диск  
    downloaded_file = bot.download_file(file_info.file_path)  
    file = f"{message.chat.id}_{file_id}.jpg" 
    file_name = f"img/{file}"  
    with open(file_name, 'wb') as f:  
        f.write(downloaded_file)

    manager.add_prize([file])
    bot.reply_to(message, 'Фотография загружена.')

def send_message():
    prize_id, img = manager.get_random_prize()[:2]
    manager.mark_prize_used(prize_id)
    hide_img(img)
    for user in manager.get_users():
        with open(f'hidden_img/{img}', 'rb') as photo:
            bot.send_photo(user, photo, reply_markup=gen_markup(id = prize_id))
        

def shedule_thread():
    schedule.every().minute.do(send_message) # Здесь ты можешь задать периодичность отправки картинок
    while True:
        schedule.run_pending()
        time.sleep(1)

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    if user_id in manager.get_users():
        bot.reply_to(message, "Ты уже зарегестрирован!")
    else:
        manager.add_user(user_id, message.from_user.username)
        bot.reply_to(message, """Привет! Добро пожаловать! 
Тебя успешно зарегистрировали!
Каждый час тебе будут приходить новые картинки и у тебя будет шанс их получить!
Для этого нужно быстрее всех нажать на кнопку 'Получить!'

Только три первых пользователя получат картинку!)""")
        

@bot.message_handler(commands=['rating'])
def handle_rating(message):
    res = manager.get_rating()
    res = [f'| @{x[0]:<11} | {x[1]:<11}|\n{"_"*26}' for x in res]
    res = '\n'.join(res)
    res = f'|USER_NAME    |COUNT_PRIZE|\n{"_"*26}\n' + res
    bot.send_message(message.chat.id, res)


@bot.message_handler(commands=['console'])
def handle_console(message):
    if message.from_user.id == adminisration:
        admin_markup = InlineKeyboardMarkup()
        admin_markup.row_width = 2 # Cколько максимум кнопок может быть в строчке
        admin_markup.add(InlineKeyboardButton("Добавить приз", callback_data="cb_first"),
                                InlineKeyboardButton('Отправить всем приз', callback_data="cb_second"),
                                InlineKeyboardButton("Обновить призы", callback_data="cb_third"))
        bot.send_message(message.chat.id, 'Консоль запущена. Выберите параметр изменения: ', reply_markup=admin_markup)
    else:
        bot.send_message(message.chat.id, 'Только администратор может использовать эту команду.')


@bot.message_handler(commands=['shop'])
def handle_shop(message):
    shop_markup = InlineKeyboardMarkup()
    shop_markup.row_width = 2 # Cколько максимум кнопок может быть в строчке
    shop_markup.add(InlineKeyboardButton("Купить бонус (15 🍫)", callback_data="cb_shop1"),
                            InlineKeyboardButton('Обновить призы (45 🍫)', callback_data='cb_shop2'))
    bot.send_message(message.chat.id, f'Магазин шоколадок\nВаше кол-во шоколадок: {manager.show_score(message.from_user.id)} 🍫 ', reply_markup=shop_markup)


# @bot.message_handler(commands=['score'])
# def get_my_score(message):
#     info = manager.get_winners_img("user_id")
#     prizes = [x[0] for x in info]
#     image_paths = os.listdir('img')
#     image_paths = [f'img/{x}' if x in prizes else f'hidden_img/{x}' for x in image_paths]
#     collage = create_collage(image_paths)

#     cv2.imshow('Collage', collage)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()

def polling_thread():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    manager = DatabaseManager(DATABASE)
    manager.create_tables()

    polling_thread = threading.Thread(target=polling_thread)
    polling_shedule  = threading.Thread(target=shedule_thread)

    polling_thread.start()
    polling_shedule.start()
