import asyncio
import logging
import time as tm
from pyowm import OWM
from pyowm.utils import config
from pyowm.utils import timestamps, formatting
from datetime import datetime, date, timedelta
from aiogram import Bot, types, utils, Dispatcher, F, Router
from aiogram.methods import StopPoll
from aiogram.filters.command import Command, Filter
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, \
KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, \
ContentType, Message, location, CallbackQuery
from geopy.geocoders import Nominatim

from config_reader import config

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.bot_token.get_secret_value())

dp = Dispatcher()

owm = OWM(config.pyowm_token.get_secret_value())
mgr = owm.weather_manager()

lat = 0.0
lon = 0.0

def show_keyboard():
	kb_quest = [
		[
			types.KeyboardButton(text="Now weather"),
			types.KeyboardButton(text="Tomorrow weather"),
			types.KeyboardButton(text="3 days weather")
		]
	]

	keyboard = types.ReplyKeyboardMarkup(
		keyboard=kb_quest,
		resize_keyboard=True,
		one_time_keyboard=True)
	tm.sleep(1)
	return keyboard

def compute_weather_three(weather, i):
	morning_message = "--------------Morning--------------"
	afternoon_message = "--------------Afternoon--------------"
	night_message = "--------------Night--------------"

	match i:
		case 0:
			time_message = morning_message
		case 1:
			time_message = afternoon_message
		case 2:
			time_message = night_message

	temp = weather.temperature('celsius')
	w_temp = temp['temp']
	w_temp_feels = temp['feels_like']
	w_wind = weather.wind()
	windness = w_wind['speed']
	w_humidity = weather.humidity
	w_status = weather.detailed_status

	weather_message = f"{time_message}\nTemp : {w_temp}°C,\nFeels like : {w_temp_feels}°C,\nWind : {windness}m/s,\nHumidity : {w_humidity}%,\nStatus : {w_status}\n"
	return weather_message

def show_weather_three(forecast_list):
	i = 0
	for weather in forecast_list:
		match i:
			case 0:
				morning = compute_weather_three(weather, i)
			case 1:
				afternoon = compute_weather_three(weather, i)
			case 2:
				night = compute_weather_three(weather, i)
		i += 1
	day_message = morning + afternoon + night
	return day_message

def show_weather_tomorrow(lat, lon):
	tomorrow_at_morning = timestamps.tomorrow(3, 0)
	tomorrow_at_afternoon = timestamps.tomorrow(9, 0)
	tomorrow_at_night = timestamps.tomorrow(18, 0)

	part_of_weather = ""
	date_message = datetime.strftime((datetime.now() + timedelta(days=1)), '%d.%m.%Y')
	weather_message = date_message + "\n"

	for i in range(3):
		match i:
			case 0:
				tomorrow_at_time = tomorrow_at_morning
				time_message = "--------------Morning--------------"
			case 1:
				tomorrow_at_time = tomorrow_at_afternoon
				time_message = "--------------Afternoon--------------"
			case 2:
				tomorrow_at_time = tomorrow_at_night
				time_message = "--------------Night--------------"
			case _:
				break

		three_h_forecaster = mgr.forecast_at_coords(lat, lon, '3h')
		weather = three_h_forecaster.get_weather_at(tomorrow_at_time)
		temp = weather.temperature('celsius')
		w_temp = temp['temp']
		w_temp_feels = temp['feels_like']
		w_wind = weather.wind()
		windness = w_wind['speed']
		w_humidity = weather.humidity
		w_status = weather.detailed_status

		part_of_weather = f"{time_message}\nTemp : {w_temp}°C,\nFeels like : {w_temp_feels}°C,\nWind : {windness}m/s,\nHumidity : {w_humidity}%,\nStatus : {w_status}\n"
		weather_message += part_of_weather

	return weather_message

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
	kb_request = [
		[
			types.KeyboardButton(text="Share your location", 
				request_location=True)
		],
	]

	keyboard = types.ReplyKeyboardMarkup(
		keyboard=kb_request,
		resize_keyboard=True,
		input_field_placeholder="Share your location",
		one_time_keyboard=True)
	await message.answer("Share your location :", reply_markup=keyboard)

@dp.message(F.location)
async def handle_location(message: types.Message):
	global lat
	global lon

	lat = message.location.latitude
	lon = message.location.longitude

	geolocator = Nominatim(user_agent="my_geo_app")
	geolocation = geolocator.reverse(str(lat) + "," + str(lon))
	address = geolocation.raw["address"]
	county = address.get('county', '')
	country = address.get('country', '')

	await message.reply(f"Country : {country} \nCounty : {county}", reply_markup=ReplyKeyboardRemove())

	await message.answer("Choose the function", reply_markup=show_keyboard())

@dp.message(F.text.lower() == 'now weather')
async def handle_now(message: Message):
	global lat
	global lon

	obs = mgr.weather_at_coords(lat, lon)
	w = obs.weather

	temp = w.temperature('celsius')
	w_temp = temp['temp']
	w_temp_feels = temp['feels_like']
	w_wind = w.wind()
	windness = w_wind['speed']
	w_humidity = w.humidity
	w_status = w.detailed_status
	weather_message = f"Temp : {w_temp}°C,\nFeels like : {w_temp_feels}°C,\nWind : {windness}m/s,\nHumidity : {w_humidity}%,\nStatus : {w_status}"
		
	await message.answer(weather_message, reply_markup=ReplyKeyboardRemove())

	await message.answer("Anything else?", reply_markup=show_keyboard())

@dp.message(F.text.lower() == "tomorrow weather")
async def handle_tomorrow(message: types.Message):
	global lat
	global lon

	await message.answer(f"{show_weather_tomorrow(lat, lon)}", reply_markup=ReplyKeyboardRemove())

	await message.answer("Anything else?", reply_markup=show_keyboard())

@dp.message(F.text.lower() == "3 days weather")
async def handle_three_days(message: types.Message):
	global lat
	global lon

	three_h_forecast = mgr.forecast_at_coords(lat, lon, '3h').forecast
	today = datetime.today()
	today_str = datetime.strftime(today, '%Y-%m-%d')
	today_strp = datetime.strptime(today_str, '%Y-%m-%d')
	today_hours = today_strp + timedelta(hours=6)
	day_1st = today_hours + timedelta(days=1)
	day_2nd = day_1st + timedelta(days=1)
	day_3rd = day_2nd + timedelta(days=1)

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

		if(insert_date(day_1st, -1) < date_time_str < insert_date(day_1st, 3)) or (insert_date(day_1st, 4) < date_time_str < insert_date(day_1st, 6)) or (insert_date(day_1st, 16) < date_time_str < insert_date(day_1st, 19)):
			first_forecast.append(weather)
			first_date = datetime.strftime(datetime.fromisoformat(date_time), '%d.%m.%Y')

		elif(insert_date(day_2nd, -1) < date_time_str < insert_date(day_2nd, 3)) or (insert_date(day_2nd, 4) < date_time_str < insert_date(day_2nd, 6)) or (insert_date(day_2nd, 16) < date_time_str < insert_date(day_2nd, 19)):
			second_forecast.append(weather)
			second_date = datetime.strftime(datetime.fromisoformat(date_time), '%d.%m.%Y')

		elif(insert_date(day_3rd, -1) < date_time_str < insert_date(day_3rd, 3)) or (insert_date(day_3rd, 4) < date_time_str < insert_date(day_3rd, 6)) or (insert_date(day_3rd, 16) < date_time_str < insert_date(day_3rd, 19)):
			third_forecast.append(weather)
			third_date = datetime.strftime(datetime.fromisoformat(date_time), '%d.%m.%Y')

	await message.answer(f"{first_date} \n{show_weather_three(first_forecast)}", reply_markup=ReplyKeyboardRemove())
	await message.answer(f"{second_date} \n{show_weather_three(second_forecast)}")
	await message.answer(f"{third_date} \n{show_weather_three(third_forecast)}")

	await message.answer("Anything else?", reply_markup=show_keyboard())

@dp.message(Command('help'))
async def cmd_help(message: types.Message):
	message_help = "Please enter the command /start and provide your location.\n(If you are using Telegram Desktop, please note that your location will not be sent. Instead, please use Telegram Mobile.)\nNext, click on the button to view the weather."
	await message.answer(message_help, reply_markup=ReplyKeyboardRemove())

async def main():
	await dp.start_polling(bot)

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	asyncio.run(main())
