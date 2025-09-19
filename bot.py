from __future__ import annotations

from typing import Callable, Sequence

import openai
import pyowm
from pyowm.commons.exceptions import PyOWMError
from pyowm.weatherapi25.weather import Weather
import telebot
from telebot import types

import apikeys


OWM_CLIENT = pyowm.OWM(apikeys.APIKEY)
WEATHER_MANAGER = OWM_CLIENT.weather_manager()

openai.api_key = apikeys.aikey
OPENAI_ENGINE = "text-davinci-003"

bot = telebot.TeleBot(apikeys.telegramkey)


THEMES = ("Погода", "Физика", "ИИ", "Об Авторе")
PHYS_THEMES = (
    "Сила тяжести",
    "Плотность",
    "Прямолинейное движение",
    "Давление",
    "Сила Архимеда",
)

WEATHER_STATUSES = {
    "Thunderstorm": ("Гроза", "⛈"),
    "Drizzle": ("Мелкий дождь", "🌧"),
    "Rain": ("Дождь", "🌧"),
    "Snow": ("Снег", "❄"),
    "Mist": ("Туман", "🌫"),
    "Smoke": ("Туман", "🌫"),
    "Haze": ("Туман", "🌫"),
    "Dust": ("Пыльно", "🕸"),
    "Fog": ("Туман", "🌫"),
    "Sand": ("Пыльно", "🕸"),
    "Ash": ("Пепел", "🦂"),
    "Squall": ("Ветренно", "🌬"),
    "Tornado": ("Торнадо", "🌪"),
    "Clear": ("Ясно", "☀"),
    "Clouds": ("Облачно", "☁"),
}

RECOMMENDED_WEAR = (
    "Оденьтесь потеплее!",
    "Не забудьте зонт!",
    "Наденьте тёплую шапку!",
    "Наденьте маску!",
    "Идите в шортах!",
)

ABOUT_AUTHOR = (
    "Привет меня зовут Батыр, мне 16 лет. Я начинающий программист💻 и разработчик игр🎮.\n\n"
    "Пишу на Python и C#. Осваиваю игровой движок Unity🖥🖱 для будущей карьеры."
)


def send_menu(
    message: telebot.types.Message,
    options: Sequence[str],
    prompt: str,
    next_handler: Callable[[telebot.types.Message], None],
) -> None:
    """Send a keyboard with the specified options and register the next handler."""

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for option in options:
        markup.add(option)
    bot.send_message(message.chat.id, prompt, reply_markup=markup)
    bot.register_next_step_handler(message, next_handler)


def send_theme_menu(message: telebot.types.Message) -> None:
    send_menu(message, THEMES, "Выберите область", handle_theme_choice)


def prompt_for_city(message: telebot.types.Message) -> None:
    bot.send_message(message.chat.id, "Введите город", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, handle_city_response)


def prompt_for_ai(message: telebot.types.Message) -> None:
    bot.send_message(message.chat.id, "Введите запрос", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, ask_openai)


def ask_openai(message: telebot.types.Message) -> None:
    prompt = message.text.strip()
    if not prompt:
        bot.send_message(message.chat.id, "Пожалуйста, введите непустой запрос.")
        bot.register_next_step_handler(message, ask_openai)
        return

    try:
        completion = openai.Completion.create(
            engine=OPENAI_ENGINE,
            prompt=prompt,
            temperature=0.5,
            max_tokens=3500,
        )
    except openai.error.OpenAIError as exc:  # type: ignore[attr-defined]
        bot.send_message(message.chat.id, f"Не удалось получить ответ: {exc}")
        send_theme_menu(message)
        return

    answer = completion.choices[0]["text"].strip()
    bot.send_message(message.chat.id, answer or "Ответ пуст.")
    send_theme_menu(message)


def handle_city_response(message: telebot.types.Message) -> None:
    city = message.text.strip()
    if not city:
        bot.send_message(
            message.chat.id,
            "Название города не должно быть пустым. Попробуйте снова.",
        )
        bot.register_next_step_handler(message, handle_city_response)
        return

    send_weather_info(message, city)


def send_weather_info(message: telebot.types.Message, city: str) -> None:
    try:
        weather = WEATHER_MANAGER.weather_at_place(city).weather
    except PyOWMError as exc:
        bot.send_message(message.chat.id, f"Не удалось получить погоду: {exc}")
        send_theme_menu(message)
        return

    response = build_weather_message(weather)
    bot.send_message(message.chat.id, response)
    send_theme_menu(message)


def build_weather_message(weather: Weather) -> str:
    status_code = weather.status
    status_name, status_icon = WEATHER_STATUSES.get(status_code, (status_code, ""))
    temperature_info = weather.temperature(unit="celsius")
    humidity = weather.humidity
    pressure = weather.pressure
    wind = weather.wind()
    visibility = weather.visibility_distance

    lines = [f"{status_name} {status_icon}".strip()]
    temperature = temperature_info.get("temp")
    feels_like = temperature_info.get("feels_like")
    if temperature is not None:
        lines.append(f"Температура: {round(temperature)} ℃")
    if feels_like is not None:
        lines.append(f"Ощущается как: {round(feels_like)} ℃")
    lines.append(f"Влажность: {humidity} %")

    wind_speed = wind.get("speed")
    if wind_speed is not None:
        lines.append(f"Скорость ветра: {round(wind_speed)} м/с")
    wind_gust = wind.get("gust")
    if wind_gust is not None:
        lines.append(f"Порывы ветра: {round(wind_gust)} м/с")

    pressure_value = pressure.get("press") if pressure else None
    if pressure_value is not None:
        lines.append(f"Давление: {round(pressure_value * 0.725)} мм рт.ст")
    if visibility is not None:
        lines.append(f"Видимость: {round(visibility / 1000, 1)} км")

    lines.extend(recommend_clothes(status_name, temperature))
    return "\n".join(lines)


def recommend_clothes(status_name: str, temperature: float | None) -> list[str]:
    recommendations: list[str] = []
    if temperature is None:
        return recommendations

    if temperature > 25:
        recommendations.append(RECOMMENDED_WEAR[4])
    if status_name in {"Пыльно", "Пепел"}:
        recommendations.append(RECOMMENDED_WEAR[3])
    if status_name == "Снег" or temperature < 0:
        recommendations.append(RECOMMENDED_WEAR[2])
    if status_name in {"Гроза", "Мелкий дождь", "Дождь"}:
        recommendations.append(RECOMMENDED_WEAR[1])
    if 0 < temperature < 15:
        recommendations.append(RECOMMENDED_WEAR[0])

    return recommendations


def handle_theme_choice(message: telebot.types.Message) -> None:
    if message.text == THEMES[0]:
        prompt_for_city(message)
    elif message.text == THEMES[1]:
        send_menu(message, PHYS_THEMES, "Выбери тему", handle_physics_choice)
    elif message.text == THEMES[2]:
        prompt_for_ai(message)
    elif message.text == THEMES[3]:
        bot.send_message(
            message.chat.id,
            ABOUT_AUTHOR,
            reply_markup=types.ReplyKeyboardRemove(),
        )
        send_theme_menu(message)
    else:
        bot.send_message(
            message.chat.id,
            "Не понимаю команду. Пожалуйста, выберите вариант из меню.",
        )
        send_theme_menu(message)


def handle_physics_choice(message: telebot.types.Message) -> None:
    bot.send_message(
        message.chat.id,
        "Раздел с задачами по физике находится в разработке.",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    send_theme_menu(message)


@bot.message_handler(commands=["start"])
def handle_start(message: telebot.types.Message) -> None:
    send_theme_menu(message)


@bot.message_handler(commands=["погода"])
def handle_weather_command(message: telebot.types.Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) == 2:
        send_weather_info(message, parts[1])
    else:
        prompt_for_city(message)


@bot.message_handler(commands=["ии"])
def handle_ai_command(message: telebot.types.Message) -> None:
    prompt_for_ai(message)


@bot.message_handler(commands=["физика"])
def handle_physics_command(message: telebot.types.Message) -> None:
    send_menu(message, PHYS_THEMES, "Выбери тему", handle_physics_choice)


def main() -> None:
    bot.polling(none_stop=True)


if __name__ == "__main__":
    main()
