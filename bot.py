import telebot
import pyowm
import openai
import time
import apikeys
from telebot import types

OpenWMap=pyowm.OWM(apikeys.APIKEY)

openai.api_key = apikeys.aikey
engine="text-davinci-003"

THEMES = ["Погода", "Физика", "ИИ", "Об Авторе"]

WEATHER_STATUSES = {}
WEATHER_STATUSES["Thunderstorm"] = ["Гроза", "⛈"]
WEATHER_STATUSES["Drizzle"] = ["Мелкий дождь", "🌧"]
WEATHER_STATUSES["Rain"] = ["Дождь", "🌧"]
WEATHER_STATUSES["Snow"] = ["Снег", "❄"]
WEATHER_STATUSES["Mist"] = ["Туман", "🌫"]
WEATHER_STATUSES["Smoke"] = ["Туман", "🌫"]
WEATHER_STATUSES["Haze"] = ["Туман", "🌫"]
WEATHER_STATUSES["Dust"] = ["Пыльно", "🕸"]
WEATHER_STATUSES["Fog"] = ["Туман", "🌫"]
WEATHER_STATUSES["Sand"] = ["Пыльно", "🕸"]
WEATHER_STATUSES["Ash"] = ["Пепел", "🦂"]
WEATHER_STATUSES["Squall"] = ["Ветренно", "🌬"]
WEATHER_STATUSES["Tornado"] = ["Торнадо", "🌪"]
WEATHER_STATUSES["Clear"] = ["Ясно", "☀"]
WEATHER_STATUSES["Clouds"] = ["Облачно", "☁"]

RECOMMENDED_WEAR = ("Оденьтесь потеплее!", "Не забудьте зонт!", "Наденьте тёплую шапку!",
"Наденьте маску!", "Идите в шортах!")

PHYS_THEMES = ("Сила тяжести", "Плотность", "Прямолинейное движение", "Давление", "Сила Архимеда")
MOVEMENT_TYPES = ("Равномерное", "Равноускоренное")
MOVEMENT_CATEGORIES = ["Расстояние", "Скорость", "Время"]
ACCELERATION = "Ускорение"
UNIFORM_MOVEMENT_DIRECTIONS = ('Введи значение скорости(м/с) и времени(с) через пробел', 'Введи значение расстояния(м) и времени(с) через пробел',
'Введи значение расстояния(м) и скорости(м/с) через пробел')

UNIFORM_ACCELERATED_MOVEMENT_DIRECTIONS = ('Введи значения начальной скорости(м/с), времени(с) и ускорения(м/с²) через пробел',
'Введи значения начальной скорости(м/с), времени(с) и ускорения(м/с²) через пробел',
'Введи значения начальной скорости(м/с), текущей скорости(м/с) и ускорения(м/с²) через пробел',
'Введи значения начальной скорости(м/с), текущей скорости(м/с) и времени(с) через пробел')

about_author = "Привет меня зовут Батыр, мне 16 лет. Я начинающий программист💻 и разработчик игр🎮.\n\nПишу на Python и C#. Осваиваю игровой движок Unity🖥🖱 для будущей карьеры."

g = 9.8

bot = telebot.TeleBot(apikeys.telegramkey)

city = ''

movement_type = ''
directions = []

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    text = message.text
    if text.find("/погода") != -1:
        global city
        city = text.split()[1]
        get_weather(message)
    if text.find("/ии") != -1:
        ask(message)

    if text.find("/физика") != -1:
        get_keyboard(message, PHYS_THEMES, "Выбери тему")

        bot.register_next_step_handler(message, get_answer)
    else:
        get_keyboard(message, THEMES, "Выберите область")

        bot.register_next_step_handler(message, get_answer)

def ask(message):
    completion = openai.Completion.create(engine=engine, prompt=message.text, temperature=0.5, max_tokens=3500)

    bot.send_message(message.from_user.id, completion.choices[0]['text'])

    time.sleep(1)

    get_keyboard(message, THEMES, "Выберите область")
    bot.register_next_step_handler(message, get_answer)    

def get_weather(message):
    global city

    if len(city) == 0:
        city = message.text

    Weather = OpenWMap.weather_manager().weather_at_place(city)
    Data = Weather.weather
    temp = Data.temperature(unit='celsius')
    
    humidity = Data.humidity
    
    pressure = Data.pressure

    status = Data.status

    visibillity_distance = Data.visibility_distance

    wind = Data.wind()

    city = ''

    show_info(message, status, temp, humidity, wind, pressure, visibillity_distance)

def show_info(message, status,temp, humidity, wind, pressure, visibillity_distance):
    info = WEATHER_STATUSES[status][0] + " " + WEATHER_STATUSES[status][1] + "\n"
    info = info + "Температура: " + str(round(temp["temp"])) + " ℃" + "\n"
    info = info + "Ощущается как: " + str(round(temp["feels_like"])) + " ℃" + "\n"
    info = info + "Влажность: " + str(humidity) + " %" "\n"
    info = info + "Скорость ветра " + str(round(wind["speed"])) + " м/с" + "\n"
    info = info + "Порывы ветра: " + str(round(wind["gust"])) + " м/с" + "\n"
    info = info + "Давление: " + str(round(pressure["press"] * 0.725)) + " мм рт.ст" + "\n"
    info = info + "Видимость: " + str(visibillity_distance / 1000) + " км" + "\n"
    
    if temp["temp"] > 25:
        info = info + RECOMMENDED_WEAR[4]
    if WEATHER_STATUSES[status][0] == "Пыльно" or WEATHER_STATUSES[status][0] == "Пепел":
        info = info + RECOMMENDED_WEAR[3]
    if WEATHER_STATUSES[status][0] == "Снег" or temp["temp"] < 0:
        info = info + RECOMMENDED_WEAR[2] 
    if WEATHER_STATUSES[status][0] == "Гроза" or WEATHER_STATUSES[status][0] == "Мелкий дождь" or WEATHER_STATUSES[status][0] == "Дождь":
        info = info + RECOMMENDED_WEAR[1]
    if temp["temp"] > 0 and temp["temp"] < 15:
        info = info + RECOMMENDED_WEAR[0]

    bot.send_message(message.from_user.id, info)

    time.sleep(1)

    get_keyboard(message, THEMES, "Выберите область")
    bot.register_next_step_handler(message, get_answer)

def get_keyboard(message, elements, direction):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

    for item in elements:
        markup.add(item)
        
    bot.send_message(message.from_user.id, direction, reply_markup = markup)

@bot.message_handler(content_types=['text'])
def get_answer(message):
    keyboard_hider = telebot.types.ReplyKeyboardRemove()

    if message.text == THEMES[0]:
        bot.send_message(message.chat.id, 'Введите город', reply_markup = keyboard_hider)
        bot.register_next_step_handler(message, get_weather)
    elif message.text == THEMES[3]:
        bot.send_message(message.chat.id, about_author, reply_markup = keyboard_hider)
    elif message.text == THEMES[2]:
        bot.send_message(message.chat.id, 'Введите запрос', reply_markup = keyboard_hider)
        bot.register_next_step_handler(message, ask)
    elif message.text == THEMES[1]:
        get_keyboard(message, PHYS_THEMES, "Выбери тему")
        bot.register_next_step_handler(message, get_answer)
    elif message.text == PHYS_THEMES[0]:
        bot.send_message(message.chat.id, 'Введи значение массы (кг)', reply_markup = keyboard_hider)
        bot.register_next_step_handler(message, calculateForceOfGravity)
    elif message.text == PHYS_THEMES[1]:
        bot.send_message(message.chat.id, 'Введи значение массы (кг) и объёма (м³) через пробел', reply_markup = keyboard_hider)
        bot.register_next_step_handler(message, calculateDensity)
    elif message.text == PHYS_THEMES[2]:
        get_keyboard(message, MOVEMENT_TYPES, 'Выбери тип движения')
        bot.register_next_step_handler(message, get_answer)
    elif message.text == PHYS_THEMES[3]:
        bot.send_message(message.chat.id, "Введи значения силы (Н) и площади(S) через пробел", reply_markup=keyboard_hider)
        bot.register_next_step_handler(message, calculatePressure)
    elif message.text == PHYS_THEMES[4]:
        bot.send_message(message.chat.id, "Введи значения плотности (кг/м³) и объёма (м³) через пробел", reply_markup=keyboard_hider)
        bot.register_next_step_handler(message, calculateForceOfArchimedes)
    elif MOVEMENT_TYPES.count(message.text):
        global movement_type, directions

        movement_type = message.text

        if movement_type == MOVEMENT_TYPES[1]:
            MOVEMENT_CATEGORIES.append(ACCELERATION)
            directions = UNIFORM_ACCELERATED_MOVEMENT_DIRECTIONS
        else:
            try:
                MOVEMENT_CATEGORIES.remove(ACCELERATION)
            except:
                pass
            directions = UNIFORM_MOVEMENT_DIRECTIONS

        get_keyboard(message, MOVEMENT_CATEGORIES, "Выбери величину")
        bot.register_next_step_handler(message, get_answer)

    if message.text == MOVEMENT_CATEGORIES[0]:
        bot.send_message(message.chat.id, directions[0], reply_markup = keyboard_hider)
        bot.register_next_step_handler(message, calculateDistance)
    elif message.text == MOVEMENT_CATEGORIES[1]:
        bot.send_message(message.chat.id, directions[1], reply_markup = keyboard_hider)                    
        bot.register_next_step_handler(message, calculateVelocity)
    elif message.text == MOVEMENT_CATEGORIES[2]:
        bot.send_message(message.chat.id, directions[2], reply_markup = keyboard_hider)                    
        bot.register_next_step_handler(message, calculateTime)
    if movement_type == MOVEMENT_TYPES[1]:
        if message.text == MOVEMENT_CATEGORIES[3]:
            bot.send_message(message.chat.id, directions[3], reply_markup = keyboard_hider)                    
            bot.register_next_step_handler(message, calculateAcceleration)

def calculateForceOfGravity(message):
    m = float(message.text)
    F = round(m * g, 2)

    solution = "Сила = " + str(F) + " Н" 

    bot.send_message(message.chat.id, solution)

def calculateDensity(message):
    values = message.text.split()

    m = float(values[0])
    v = float(values[1])
    d = m / v

    if d < 1000:
        d = round(d, 1)
    else:
        d = round(d)
    
    solution = "Плотность(ρ) = " + str(d) + " кг/м³"
    bot.send_message(message.chat.id, solution)

def calculateDistance(message):
    values = message.text.split()

    if movement_type == MOVEMENT_TYPES[0]:
        v = float(values[0])
        t = float(values[1])

        s = round(v * t, 2)
        solution = "Расстояние(S) = " + str(s) + " м"
    else:
        v = float(values[0])
        t = float(values[1])
        a = float(values[2])

        s = round(v * t + (a * pow(t, 2)) / 2, 2)
        solution = "Расстояние(S) = " + str(s) + " м"

    bot.send_message(message.chat.id, solution)

def calculateVelocity(message):
    values = message.text.split()

    if movement_type == MOVEMENT_TYPES[0]:
        s = float(values[0])
        t = float(values[1])

        v = round(s / t, 2)
        solution = "Скорость(м/с) = " + str(v) + " м/с"
    else:
        v = float(values[0])
        t = float(values[1])
        a = float(values[2])

        v = round(v + a * t, 2)
        solution = "Скорость(м/с) = " + str(v) + " м/с"
    
    bot.send_message(message.chat.id, solution)

def calculateTime(message):
    values = message.text.split()

    if movement_type == MOVEMENT_TYPES[0]:
        s = float(values[0])
        v = float(values[1])

        t = round(s / v, 2)
        solution = "Время(с) = " + str(t) + " с"
    else:
        v_0 = float(values[0])
        v = float(values[1])
        a = float(values[2])

        t = abs(round((v - v_0) / a, 2))
        solution = "Время(с) = " + str(t) + " с"
    bot.send_message(message.chat.id, solution)

def calculateAcceleration(message):
    values = message.text.split()

    v_0 = float(values[0])
    v = float(values[1])
    t = float(values[2])

    a = abs(round((v - v_0) / t, 2))
    solution = "Ускорение(м/с²) = " + str(a) + " м/с²"

    bot.send_message(message.chat.id, solution)

def calculatePressure(message):
    values = message.text.split()

    f = float(values[0])
    s = float(values[1])

    p = round(f / s, 2)
    solution = "Давление (P) = " + str(p) + " Па"

    bot.send_message(message.chat.id, solution)

def calculateForceOfArchimedes(message):
    values = message.text.split()

    d = float(values[0])
    v = float(values[1])

    f = round(d * g * v, 2)

    solution = "Сила Архимеда (Н) = " + str(f) + " Н"

    bot.send_message(message.chat.id, solution)

if __name__ == '__main__':
    bot.infinity_polling()