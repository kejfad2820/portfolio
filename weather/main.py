import asyncio
import logging
import requests
import pytz
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

def show_weather_today(forecast_list):
	for weather in forecast_list:
		date = weather.reference_time('iso')
		temp = weather.temperature('celsius')
		w_temp = temp['temp']
		w_temp_feels = temp['feels_like']
		w_wind = weather.wind()
		windness = w_wind['speed']
		w_humidity = weather.humidity
		w_status = weather.detailed_status

		weather_message = f"Temp : {w_temp}°C,\nFeels like : {w_temp_feels}°C,\nWind : {windness}m/s,\nHumidity : {w_humidity}%,\nStatus : {w_status}"
		return weather_message

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

	'''tf = TimezoneFinder()
	tzn = tf.timezone_at(lng=lon, lat=lat)
	timezone_str = tzn
	timezone = pytz.timezone(timezone_str)

	forecast = mgr.forecast_at_coords(lat, lon, interval='3h')
	# Словари для хранения данных
	morning_forecast = []
	day_forecast = []
	evening_forecast = []

	# Определяем временные рамки для утреннего, дневного и вечернего прогноза
	for weather in forecast.forecast:
	    time = weather.reference_time('iso')
	    time_utc = datetime.fromisoformat(time.replace('Z', '+00:00'))
	    local_time = time_utc.astimezone(timezone)  # Преобразуем в московское время

	    hour = local_time.hour  # Получаем час

	    # Группируем прогнозы
	    if 5 <= hour < 9:  # Утро с 5 до 8
	        morning_forecast.append(weather)
	    elif 12 <= hour < 16:  # День с 12 до 15
	        day_forecast.append(weather)
	    elif 20 <= hour < 22:  # Вечер с 21 до 22
	        evening_forecast.append(weather)

	await message.answer(f"Today's morning : \n{show_weather_today(morning_forecast)}")
	await message.answer(f"Today's afternoon : \n{show_weather_today(day_forecast)}")
	await message.answer(f"Today's night : \n{show_weather_today(evening_forecast)}")'''

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

	obs = mgr.weather_at_coords(float(lat), float(lon))
	w = obs.weather

async def main():
	await dp.start_polling(bot)

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	asyncio.run(main())