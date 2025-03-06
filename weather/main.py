import asyncio
import logging
from aiogram import Bot, types, utils, Dispatcher, F, Router
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, \
KeyboardButton, Message, location
from geopy.geocoders import Nominatim
from deep_translator import GoogleTranslator

from config_reader import config 	#	Файл с токенами бота и pyowm
from weather_calcing import calc	#	Файл с функциями погоды

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.bot_token.get_secret_value())

dp = Dispatcher()

lat = 0.0	#	дефолтная широта
lon = 0.0	#	дефолтная долгота
lang = "english"	#	дефолтный язык интерфейса

#		Переменные для хэндлеров		#

now_message_en = "current weather"
now_message_ru = "текущая погода"
tomorrow_message_en = "weather for tomorrow"
tomorrow_message_ru = "погода на завтра"
three_message_en = "weather for 3 days"
three_message_ru = "погода в течение 3 дней"

def open_keyboard(lang: str, message: str):		#	Функция перевода текста для клавиатуры
	translator = GoogleTranslator(source='auto', target=lang)
	open_keyboard_message = translator.translate(message)
	return open_keyboard_message

def show_keyboard():	#	Функция вызова клавиатуры с выбором погоды
	global lang

	kb_quest = [
		[
			KeyboardButton(text=open_keyboard(lang, "Current weather")),
			KeyboardButton(text=open_keyboard(lang, "Weather for tomorrow"))
			
		],
		[
			KeyboardButton(text=open_keyboard(lang, "Weather for 3 days"))
		]
	]

	keyboard = ReplyKeyboardMarkup(keyboard=kb_quest, resize_keyboard=True, one_time_keyboard=True)
	return keyboard

@dp.message(Command('start'))
async def cmd_start(message: Message):	#	Функция команды /start
	global lang

	kb_request = [[KeyboardButton(text=open_keyboard(lang, "Please share your location"), 
		request_location=True)]]

	keyboard = ReplyKeyboardMarkup(keyboard=kb_request, resize_keyboard=True,
		input_field_placeholder=open_keyboard(lang, "Please share your location"),
		one_time_keyboard=True)
	await message.answer(open_keyboard(lang, 
		"Please share your location\nIf you want to change the language, call the command /lang"), 
		reply_markup=keyboard)

@dp.message(Command('lang'))
async def cmd_lang(message: Message):	#	 Функция выбора языка
	global lang

	translator = GoogleTranslator(source='auto', target=lang)

	eng_message = translator.translate("English")
	rus_message = translator.translate("Russian")
	kb_request = [
		[
			KeyboardButton(text=eng_message),
			KeyboardButton(text=rus_message)
		]
	]

	keyboard = ReplyKeyboardMarkup(keyboard=kb_request, resize_keyboard=True,
		input_field_placeholder=open_keyboard(lang, "Choose the language"),
		one_time_keyboard=True)

	await message.answer(open_keyboard(lang, "Choose the language"), reply_markup=keyboard)

@dp.message(F.text.lower() == "английский")
@dp.message(F.text.lower() == "english")
async def cmd_eng(message: Message):	#	Функция изменения языка на английский
	global lang
	lang = 'english'

	kb_start = [[KeyboardButton(text="/start")]]
	keyboard = ReplyKeyboardMarkup(keyboard=kb_start, resize_keyboard=True,
		input_field_placeholder="Restart the bot",
		one_time_keyboard=True)

	lang_message = "Hello, please restart the bot"
	await message.answer(lang_message, reply_markup=keyboard)

@dp.message(F.text.lower() == "русский")
@dp.message(F.text.lower() == "russian")
async def cmd_rus(message: Message):	#	Функция изменения языка на русский
	global lang
	lang = 'russian'

	kb_start = [[KeyboardButton(text="/start")]]
	keyboard = ReplyKeyboardMarkup(keyboard=kb_start, resize_keyboard=True, 
		input_field_placeholder="Перезапустите бота",
		one_time_keyboard=True)

	await message.answer(open_keyboard(lang, "Приветствую вас, пожалуйста перезапустите бота"), 
		reply_markup=keyboard)

@dp.message(F.location)
async def handle_location(message: Message):	#	Функция получения и инициализации геолокации от пользователя
	global lat
	global lon
	global lang

	translator = GoogleTranslator(source='auto', target=lang)

	lat = message.location.latitude		#	Перезапись широты
	lon = message.location.longitude	#	Перезапись долготы

	geolocator = Nominatim(user_agent="my_geo_app")		#	Инициализация фреймворка для проверки правильности получения геолокации
	geolocation = geolocator.reverse(str(lat) + "," + str(lon))
	address = geolocation.raw["address"]
	county = address.get('county', '')		#	Получение региона по долготе и широте
	country = address.get('country', '')	#	Получение страны по долготе и широте

	country_message = "Country"
	country_message = translator.translate(country_message) + " : " + translator.translate(str(country))	#	Сообщение с выводом страны пользователя с возможностью перевода на другой язык интерфейса
	county_message = "Region"
	county_message = translator.translate(county_message) + " : " + translator.translate(str(county))		#	Сообщение с выводом региона пользователя с возможносью перевода

	await message.reply(f"{country_message}\n{county_message}", reply_markup=ReplyKeyboardRemove())		#	Вывод геолокации
	await message.answer(open_keyboard(lang, "Please choose the function"), reply_markup=show_keyboard())	#	Открытие клавиатуры с выбором погоды

@dp.message(F.text.lower() == now_message_en)
@dp.message(F.text.lower() == now_message_ru)
async def handle_now(message: Message):		#	Нажатие на кнопку "Текущая погода"
	global lat
	global lon
	global lang

	await message.answer(calc.calc_weather_now(lang, lat, lon))	#	Вывод функции текущей погоды
	await message.answer(open_keyboard(lang, "Anything else?"), reply_markup=show_keyboard())	#	Открытие клавиатуры для дальнейших действий

@dp.message(F.text.lower() == tomorrow_message_en)
@dp.message(F.text.lower() == tomorrow_message_ru)
async def handle_tomorrow(message: Message):	#	Нажатие на кнопку "Погода на завтра"
	global lat
	global lon
	global lang

	await message.answer(calc.calc_weather_tomorrow(lang, lat, lon))	#	Вывод функции завтрашней погоды
	await message.answer(open_keyboard(lang, "Anything else?"), reply_markup=show_keyboard())	#	Открытие клавиатуры для дальнейших действий

@dp.message(F.text.lower() == three_message_en)
@dp.message(F.text.lower() == three_message_ru)
async def handle_three_days(message: Message):	#	Нажатие на кнопку "Погода на 3 дня"
	global lat
	global lon
	global lang

	await message.answer(calc.show_weather_three(lang, lat, lon, 1))	#	Вывод первого дня
	await message.answer(calc.show_weather_three(lang, lat, lon, 2))	#	Вывод второго дня
	await message.answer(calc.show_weather_three(lang, lat, lon, 3))	#	Вывод третьего дня

<<<<<<< HEAD
	await message.answer(open_keyboard(lang, "Anything else?"), reply_markup=show_keyboard())	#	Открытие клавиатуры для дальнейших действий
=======
	first_forecast = []
	second_forecast = []
	third_forecast = []

	first_date = ""
	second_date = ""
	third_date = ""

	def insert_date(day_x, hours):
		day_x = (day_x + timedelta(hours=hours)).timestamp()
		return day_x

	for weather in three_h_forecast:
		date_time = weather.reference_time('iso')
		date_time_str = datetime.fromisoformat(date_time).timestamp()

		if(insert_date(day_1st, -1) < date_time_str < insert_date(day_1st, 3)) or (insert_date(day_1st, 4) < date_time_str < insert_date(day_1st, 7)) or (insert_date(day_1st, 16) < date_time_str < insert_date(day_1st, 19)):
			first_forecast.append(weather)
			first_date = datetime.strftime(datetime.fromisoformat(date_time), '%d.%m.%Y')

		elif(insert_date(day_2nd, -1) < date_time_str < insert_date(day_2nd, 3)) or (insert_date(day_2nd, 4) < date_time_str < insert_date(day_2nd, 7)) or (insert_date(day_2nd, 16) < date_time_str < insert_date(day_2nd, 19)):
			second_forecast.append(weather)
			second_date = datetime.strftime(datetime.fromisoformat(date_time), '%d.%m.%Y')

		elif(insert_date(day_3rd, -1) < date_time_str < insert_date(day_3rd, 3)) or (insert_date(day_3rd, 4) < date_time_str < insert_date(day_3rd, 7)) or (insert_date(day_3rd, 16) < date_time_str < insert_date(day_3rd, 19)):
			third_forecast.append(weather)
			third_date = datetime.strftime(datetime.fromisoformat(date_time), '%d.%m.%Y')

	await message.answer(f"{first_date} \n{show_weather_three(first_forecast)}", reply_markup=ReplyKeyboardRemove())
	await message.answer(f"{second_date} \n{show_weather_three(second_forecast)}")
	await message.answer(f"{third_date} \n{show_weather_three(third_forecast)}")

	await message.answer("Anything else?", reply_markup=show_keyboard())
>>>>>>> aa3bfb2caacec84f8d95176cfea7016c764acd3b

@dp.message(Command('help'))
async def cmd_help(message: Message):	#	Команда /help
	global lang

	if lang == 'english':	#	Проверка языка(условный оператор выбран из-за "трудностей" перевода гуглом)
		message_help_part_1 = "Please enter the command /start and provide your location.\n"
		message_help_part_2 = "(If you are using Telegram Desktop, please note that your location will not be sent. Instead, please use Telegram Mobile.)\n"
		message_help_part_3 = "Next, click on the button to view the weather.\nIf you're wanting to change the language enter the /lang"
		message_help = message_help_part_1 + message_help_part_2 + message_help_part_3

		await message.answer(message_help, reply_markup=ReplyKeyboardRemove())
	elif lang == "russian":
		message_help_part_1 = "Пожалуйста введите команду /start и поделитесь своей геолокацией.\n"
		message_help_part_2 = "(Если вы используете Telegram Desktop, обратите внимание, что ваше местоположение не будет отправлено. Вместо этого используйте Telegram Mobile.)\n"
		message_help_part_3 = "Затем нажмите на кнопку, чтобы посмотреть погоду.\nЕсли вы хотите изменить язык, введите команду /lang"
		message_help = message_help_part_1 + message_help_part_2 + message_help_part_3

		await message.answer(message_help, reply_markup=ReplyKeyboardRemove())

async def main():
	await dp.start_polling(bot)

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	asyncio.run(main())