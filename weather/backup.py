import asyncio
import logging
import requests
import pytz
import time as tm
from timezonefinder import TimezoneFinder
from pyowm import OWM
from pyowm.utils import config
from pyowm.utils import timestamps, formatting
#from pyowm.utils.timeutils import timeutils
from datetime import datetime, date, timedelta, time, timezone
from aiogram import Bot, types, utils, Dispatcher, F, Router
from aiogram.handlers import CallbackQueryHandler
from aiogram.filters.command import Command, Filter
from aiogram.filters.callback_data import CallbackData
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, \
KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, \
ContentType, Message, location, CallbackQuery
from geopy.geocoders import Nominatim

from config_reader import config

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.bot_token.get_secret_value())

router = Router()

dp = Dispatcher()

dp.include_router(router)

owm = OWM('040f7d6d193df83ebe09a3150d28ba81')
mgr = owm.weather_manager()

lat = 0.0
lon = 0.0

def show_weather_three(weather, i):
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

def view_weather_three(forecast_list):
	morning_message = "Morning"
	afternoon_message = "Afternoon"
	night_message = "Night"
	i = 0
	for weather in forecast_list:
		if i == 0:
			morning = show_weather_three(weather, i)
		if i == 1:
			afternoon = show_weather_three(weather, i)
		elif i == 2:
			night = show_weather_three(weather, i)
		i += 1
	day_message = morning + afternoon + night
	return day_message

def show_weather_tomorrow(tomorrow_at_time, lat, lon):
	three_h_forecaster = mgr.forecast_at_coords(lat, lon, '3h')
	weather = three_h_forecaster.get_weather_at(tomorrow_at_time)
	temp = weather.temperature('celsius')
	w_temp = temp['temp']
	w_temp_feels = temp['feels_like']

	w_wind = weather.wind()
	windness = w_wind['speed']
	w_humidity = weather.humidity
	w_status = weather.detailed_status

	weather_message = f"Temp : {w_temp}°C,\nFeels like : {w_temp_feels}°C,\nWind : {windness}m/s,\nHumidity : {w_humidity}%,\nStatus : {w_status}"

	return weather_message

#@dp.message(Command('start'))
@router.message(Command(commands=["start"]))
async def cmd_quest(message: types.Message):
	kb_request = [
		[
			types.KeyboardButton(text="Share your location", 
				request_location=True)
		],
	]

	keyboard = types.ReplyKeyboardMarkup(
		keyboard=kb_request,
		resize_keyboard=True,
		input_field_placeholder="Enter the button")
	await message.answer("Enter the function", reply_markup=keyboard)

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

	await message.reply(f"Country : {country} \nCounty : {county}")

	kb_quest = [
		[
			types.KeyboardButton(text="Now weather"),
			types.KeyboardButton(text="Tomorrow weather"),
			types.KeyboardButton(text="3 days weather")
		]
	]

	keyboard = types.ReplyKeyboardMarkup(
		keyboard=kb_quest,
		resize_keyboard=True)
	await message.answer("Enter the button", reply_markup=keyboard)

@router.message(F.text.lower() == 'now weather')
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
	
	await message.answer(weather_message)

@dp.message(F.text.lower() == "tomorrow weather")
async def handle_tomorrow(message: types.Message):
	global lat
	global lon

	obs = mgr.weather_at_coords(float(lat), float(lon))
	w = obs.weather

	now = datetime.now()
	tomorrow = now + timedelta(days=1)
	tomorrow_timestamp = int(tomorrow.timestamp())
	
	tomorrow_at_morning = timestamps.tomorrow(3, 0)
	tomorrow_at_afternoon = timestamps.tomorrow(9, 0)
	tomorrow_at_night = timestamps.tomorrow(18, 0)

	await message.answer(f"Weather for tomorrow as of 8 am : \n{show_weather_tomorrow(tomorrow_at_morning, lat, lon)}")
	await message.answer(f"Weather for tomorrow as of 2 pm : \n{show_weather_tomorrow(tomorrow_at_afternoon, lat, lon)}")
	await message.answer(f"Weather for tomorrow as of 11 pm : \n{show_weather_tomorrow(tomorrow_at_night, lat, lon)}")

@dp.message(F.text == "3 days weather")
async def handle_three_days(message: types.Message):
	global lat
	global lon

	#obs = mgr.weather_at_coords(float(lat), float(lon), '3h')
	#w = obs.weather

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
			#first_date = datetime.strftime(datetime.strptime(date_time, '%Y-%m-%d'), '%Y-%m-%d')
			#first_date_strp = datetime.strptime(date_time, '%Y-%m-%d')
			first_date = datetime.strftime(datetime.fromisoformat(date_time), '%d.%m.%Y')

		elif(insert_date(day_2nd, -1) < date_time_str < insert_date(day_2nd, 3)) or (insert_date(day_2nd, 4) < date_time_str < insert_date(day_2nd, 6)) or (insert_date(day_2nd, 16) < date_time_str < insert_date(day_2nd, 19)):
			second_forecast.append(weather)
			second_date = datetime.strftime(datetime.fromisoformat(date_time), '%d.%m.%Y')

		elif(insert_date(day_3rd, -1) < date_time_str < insert_date(day_3rd, 3)) or (insert_date(day_3rd, 4) < date_time_str < insert_date(day_3rd, 6)) or (insert_date(day_3rd, 16) < date_time_str < insert_date(day_3rd, 19)):
			third_forecast.append(weather)
			third_date = datetime.strftime(datetime.fromisoformat(date_time), '%d.%m.%Y')

		'''if(day_1st - timedelta(hours=1)).timestamp() < date_time_str < (day_1st + timedelta(hours=3)).timestamp() or (day_1st + timedelta(hours=4)).timestamp() < date_time_str < (day_1st + timedelta(hours=6)).timestamp() or (day_1st + timedelta(hours=16)).timestamp() < date_time_str < (day_1st + timedelta(hours=19)).timestamp():
			first_forecast.append(weather)

		elif(day_2nd - timedelta(hours=1)).timestamp() < date_time_str < (day_2nd + timedelta(hours=3)).timestamp() or (day_2nd + timedelta(hours=4)).timestamp() < date_time_str < (day_2nd + timedelta(hours=6)).timestamp() or (day_2nd + timedelta(hours=16)).timestamp() < date_time_str < (day_2nd + timedelta(hours=19)).timestamp():
			second_forecast.append(weather)

		elif(day_3rd - timedelta(hours=1)).timestamp() < date_time_str < (day_3rd + timedelta(hours=3)).timestamp() or (day_3rd + timedelta(hours=4)).timestamp() < date_time_str < (day_3rd + timedelta(hours=6)).timestamp() or (day_3rd + timedelta(hours=16)).timestamp() < date_time_str < (day_3rd + timedelta(hours=19)).timestamp():
			third_forecast.append(weather)'''

		'''if (day_1st - timedelta(hours=1)).timestamp() < date_time_str < (day_1st + timedelta(hours=3)).timestamp() or (day_2nd - timedelta(hours=1)).timestamp() < date_time_str < (day_2nd + timedelta(hours=3)).timestamp() or (day_3rd - timedelta(hours=1)).timestamp() < date_time_str < (day_3rd + timedelta(hours=3)).timestamp():
			#morning_forecast.append(date_time)
			morning_forecast.append(weather)
		elif (day_1st + timedelta(hours=4)).timestamp() < date_time_str < (day_1st + timedelta(hours=6)).timestamp() or (day_2nd + timedelta(hours=4)).timestamp() < date_time_str < (day_2nd + timedelta(hours=6)).timestamp() or (day_3rd + timedelta(hours=4)).timestamp() < date_time_str < (day_3rd + timedelta(hours=6)).timestamp():
			#afternoon_forecast.append(date_time)
			afternoon_forecast.append(weather)
		elif (day_1st + timedelta(hours=16)).timestamp() < date_time_str < (day_1st + timedelta(hours=19)).timestamp() or (day_2nd + timedelta(hours=16)).timestamp() < date_time_str < (day_2nd + timedelta(hours=19)).timestamp() or (day_3rd + timedelta(hours=16)).timestamp() < date_time_str < (day_3rd + timedelta(hours=19)).timestamp():
			#night_forecast.append(date_time)
			night_forecast.append(weather)
		else:
			pass'''

	#await message.answer(f"1st day: {first_forecast}")
	#await message.answer(f"2nd day: {second_forecast}")
	#await message.answer(f"3rd day: {third_forecast}")

	await message.answer(f"{first_date} \n{view_weather_three(first_forecast)}")
	await message.answer(f"{second_date} \n{view_weather_three(second_forecast)}")
	await message.answer(f"{third_date} \n{view_weather_three(third_forecast)}")
	#await message.answer(f"{first_forecast}")

async def main():
	await dp.start_polling(bot)

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	asyncio.run(main())
