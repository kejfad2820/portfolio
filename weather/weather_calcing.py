from config_reader import config 	#	Файл с токенами бота и pyowm

from pyowm import OWM
from pyowm.utils import timestamps, formatting
from datetime import datetime, date, timedelta
from deep_translator import GoogleTranslator

owm = OWM(config.pyowm_token.get_secret_value())
mgr = owm.weather_manager()

class Weather_Calculation:
	def __init__(self):
		self.self = self

	def normal_status(self, w_status: str, lang: str):	#	Функция корректного перевода погоды
		translator = GoogleTranslator('auto', lang)	#	Инициализация гугл-переводчика(язык определяет автоматически, переводит на язык, который передается из файла main.py)
		transl_w_status = translator.translate(w_status)	#	Инициализация переведенного статуса погоды

		match transl_w_status.lower():
			case "светлый снег":
				transl_w_status = " небольшой снег"
				
			case "разбросанные облака":
				transl_w_status = " переменная облачность"
				
			case "разорванные облака":
				transl_w_status = " облачно с прояснениями"
				
			case "сломанные облака":
				transl_w_status = " переменная облачность"
				
			case "чистое небо":
				transl_w_status = " солнечно"
				
			case "пасмурные облака":
				transl_w_status = " пасмурно"

			case "снег":
				transl_w_status = " снегопад"

			case "несколько облаков":
				transl_w_status = " немного облачно"
				
			case _:	#	Если переданный язык - английский, или статус не прошел проверки выше, то выводится статус без изменений
				return transl_w_status
		return transl_w_status 	#	Выдача измененного статуса


	def calc_weather_now(self, lang: str, lat: float, lon: float):	#	Функция текущей погоды
		obs = mgr.weather_at_coords(lat, lon)
		w = obs.weather

		translator = GoogleTranslator('auto', lang)

		temp = w.temperature('celsius')	#	Выдача температуры в цельсиях
		w_temp = temp['temp']
		w_temp_feels = temp['feels_like']	#	Выдача чувствующейся температуры
		w_wind = w.wind()
		windness = w_wind['speed']	#	Выдача скорости ветра
		w_humidity = w.humidity #	Выдача влажности
		w_status = w.detailed_status	#	Статус погоды(солнечно, облачно, дождь, снег и тд)

		''' Передача погоды в данный временной промежуток времени в сообщение, 
		из-за некорректного перевода переменной, переведенный статус добавляется в переменную позже 
		'''

		part_of_weather = f"Temp : {w_temp}°C,\nFeels like : {w_temp_feels}°C,\nWind : {windness}m/s,\nHumidity : {w_humidity}%,\nStatus : "
		weather_message = translator.translate(part_of_weather)
		weather_message += " " + self.normal_status(w_status, lang)
		return weather_message

	def calc_weather_tomorrow(self, lang: str, lat: float, lon: float):	#	Функция завтрашней погоды
		translator = GoogleTranslator('auto', lang)

		morning_message = "---------------Morning---------------"	#	Переменная для обозначения утра в сообщении
		afternoon_message = "--------------Afternoon--------------"	#	Переменная для обозначения полудня в сообщении
		night_message = "----------------Night----------------"	#	Переменная для обозначения ночи в сообщении

		#	Функции pyowm для завтрашней погоды, время выбрано по UTC+00

		tomorrow_at_morning = timestamps.tomorrow(3, 0)
		tomorrow_at_afternoon = timestamps.tomorrow(9, 0)
		tomorrow_at_night = timestamps.tomorrow(18, 0)

		part_of_weather = ""
		date_message = datetime.strftime((datetime.now() + timedelta(days=1)), '%d.%m.%Y')	#	Вывод завтрашней даты
		weather_message = date_message + "\n"

		for i in range(3):	#	Цикл для перебора утра, вечера и ночи
			match i:
				case 0:	#	Передается утро
					tomorrow_at_time = tomorrow_at_morning
					time_message = morning_message
				case 1:	#	Передается полдень
					tomorrow_at_time = tomorrow_at_afternoon
					time_message = afternoon_message
				case 2:	#	Передается ночь
					tomorrow_at_time = tomorrow_at_night
					time_message = night_message
				case _:
					break

			three_h_forecaster = mgr.forecast_at_coords(lat, lon, '3h')	#	Функция pyowm для инициализирования погоды каждые 3 часа
			weather = three_h_forecaster.get_weather_at(tomorrow_at_time)	#	Функция pyowm для выдачи погоды до данного времени
			temp = weather.temperature('celsius')	#	Выдача температуры в цельсиях
			w_temp = temp['temp']
			w_temp_feels = temp['feels_like']	#	Выдача чувствующейся температуры
			w_wind = weather.wind()
			windness = w_wind['speed']	#	Выдача скорости ветра
			w_humidity = weather.humidity #	Выдача влажности
			w_status = weather.detailed_status	#	Статус погоды(солнечно, облачно, дождь, снег и тд)

			''' Добавление погоды в конкретный временной промежуток в переменную сообщения всего дня
			(из-за некорректного перевода переменной, переведенный статус добавляется в переменную позже)
			'''

			part_of_weather = f"{time_message}\nTemp : {w_temp}°C,\nFeels like : {w_temp_feels}°C,\nWind : {windness}m/s,\nHumidity : {w_humidity}%,\nStatus :"
			part_of_weather = translator.translate(part_of_weather)
			part_of_weather += " " + self.normal_status(w_status, lang)
			weather_message += part_of_weather + '\n'
		return weather_message	#	Выдача погоды, разделенной на утро, день и ночь

	def print_weather_three(self, lang: str, lat: float, lon: float, weather: object, i: int):	#	Функция для непосредственных расчетов одного объекта weather
		translator = GoogleTranslator('auto', lang)

		morning_message = "---------------Morning---------------"
		afternoon_message = "--------------Afternoon--------------"
		night_message = "----------------Night----------------"

		match i:	#	Передаваемая переменная i обозначает привязанное время суток к объекту weather
			case 0:	#	Утро
				time_message = morning_message
			case 1:	#	Полдень
				time_message = afternoon_message
			case 2:	#	Ночь
				time_message = night_message
			case _:
				print("print_weather_three : error")

		temp = weather.temperature('celsius')	#	Выдача температуры в цельсиях
		w_temp = temp['temp']
		w_temp_feels = temp['feels_like']	#	Выдача чувствующейся температуры
		w_wind = weather.wind()
		windness = w_wind['speed']	#	Выдача скорости ветра
		w_humidity = weather.humidity #	Выдача влажности
		w_status = weather.detailed_status	#	Статус погоды(солнечно, облачно, дождь, снег и тд)

		''' Выдача погоды в конкретный временной промежуток
		(из-за некорректного перевода переменной, переведенный статус добавляется в переменную позже)
		'''

		part_of_weather = f"{time_message}\nTemp : {w_temp}°C,\nFeels like : {w_temp_feels}°C,\nWind : {windness}m/s,\nHumidity : {w_humidity}%,\nStatus : "
		part_of_weather = translator.translate(part_of_weather)
		weather_message = part_of_weather + " " + self.normal_status(w_status, lang)
		return weather_message

	def compute_weather_three(self, lang: str, lat: float, lon: float, forecast_list: list):	#	Функция разделения погоды на утро, полдень и ночь одного дня
		i = 0	#	Переменная для инициализирования утра, дня и ночи
		for weather in forecast_list:	#	Цикл pyowm для разделения объектов weather(в передаваемых массивах по 3 объекта weather: утро, день и ночь)
			match i:
				case 0:	#	Первый получаемый объект - погода на утро
					morning = self.print_weather_three(lang, lat, lon, weather, i)	#	Инициализирование утра
				case 1:	#	Второй получаемый объект - погода на полдень
					afternoon = self.print_weather_three(lang, lat, lon, weather, i)	#	Инициализирование полудня
				case 2:	#	Третий получаемый объект - погода на ночь
					night = self.print_weather_three(lang, lat, lon, weather, i)	#	Инициализирование ночи
				case _:
					print("compute_weather_three : error")
			i += 1
		#	Выдача погоды одного дня, разделенного на утро, полдень и ночь, непосредственно в сообщение
		day_message = morning + '\n' + afternoon + '\n' + night
		return day_message

	def show_weather_three(self, lang: str, lat: float, lon: float, i: int):	#	Функция выдачи погоды на 3 дня
		three_h_forecast = mgr.forecast_at_coords(lat, lon, '3h').forecast #	Функция pyowm для выдачи погоды каждых следующих 3х часов от нынешнего времени
		today = datetime.today()	#	Нынешнее время с годом, месяцем, днем, часом, минутами, секундами и миллисекундами
		#	Следующие 2 переменные используются для получения настоящего года, месяца и дня
		today_str = datetime.strftime(today, '%Y-%m-%d')	
		today_strp = datetime.strptime(today_str, '%Y-%m-%d')

		today_hours = today_strp + timedelta(hours=6)	#	Получение переменной с данными(Год:месяц:день:6 часов утра)
		#	Последующие переменные используются для инициализации 6 часов утра на последующие 3 дня
		day_1st = today_hours + timedelta(days=1)
		day_2nd = day_1st + timedelta(days=1)
		day_3rd = day_2nd + timedelta(days=1)

		#	Массивы для получения погоды для 3х последующих дней		
		first_forecast = []
		second_forecast = []
		third_forecast = []

		#	Переменные для последующей выдачи даты каждого из дней в сообщении
		first_date = ""
		second_date = ""
		third_date = ""

		def insert_date(day_x, hours):	#	Функция для обозначения периода времени с переводом в timestamp(для простоты сравнения)
			day_x = (day_x + timedelta(hours=hours)).timestamp()
			return day_x

		for weather in three_h_forecast:	#	Функция записи будущей погоды с шагом в 3 часа(к нынешнему времени каждый цикл прибавляет по 3 часа)
			date_time = weather.reference_time('iso')	#	Получение даты и времени из функции pyowm и перевод в string
			date_time_str = datetime.fromisoformat(date_time).timestamp()	#	Перевод даты в timestamp для упрощенной последующей проверки

			# В данном случае мы проверяем даты из функции pyowm с периодами времени последующих дней(+-6:00, +- 14:00 и +- 23:00)
			if(insert_date(day_1st, -1) < date_time_str < insert_date(day_1st, 3)) or (insert_date(day_1st, 4) < date_time_str < insert_date(day_1st, 7)) or (insert_date(day_1st, 16) < date_time_str < insert_date(day_1st, 19)):
				first_forecast.append(weather)	#	записываем объект weather в массив первого дня
				first_date = datetime.strftime(datetime.fromisoformat(date_time), '%d.%m.%Y')	#	Переводим дату в string

			elif(insert_date(day_2nd, -1) < date_time_str < insert_date(day_2nd, 3)) or (insert_date(day_2nd, 4) < date_time_str < insert_date(day_2nd, 7)) or (insert_date(day_2nd, 16) < date_time_str < insert_date(day_2nd, 19)):
				second_forecast.append(weather)	#	записываем объект weather в массив второго дня
				second_date = datetime.strftime(datetime.fromisoformat(date_time), '%d.%m.%Y')	#	Переводим дату в string

			elif(insert_date(day_3rd, -1) < date_time_str < insert_date(day_3rd, 3)) or (insert_date(day_3rd, 4) < date_time_str < insert_date(day_3rd, 7)) or (insert_date(day_3rd, 16) < date_time_str < insert_date(day_3rd, 19)):
				third_forecast.append(weather)	#	записываем объект weather в массив третьего дня
				third_date = datetime.strftime(datetime.fromisoformat(date_time), '%d.%m.%Y')	#	Переводим дату в string

		#	Цикл выдачи погоды по дням
		match i:	#	Переменную i мы передаем из файла main.py для разделения выдачи 3х дней на 3 сообщения
			case 1:
				message = f"{first_date}\n{self.compute_weather_three(lang, lat, lon, first_forecast)}"	#	Выдача результата функции вычисления погоды первого дня
				return message
			case 2:
				message = f"{second_date}\n{self.compute_weather_three(lang, lat, lon, second_forecast)}"	#	Выдача результата функции вычисления погоды второго дня
				return message
			case 3:
				message = f"{third_date}\n{self.compute_weather_three(lang, lat, lon, third_forecast)}"	#	Выдача результата функции вычисления погоды третьего дня
				return message
			case _:
				print("Incorrect input")

calc = Weather_Calculation()