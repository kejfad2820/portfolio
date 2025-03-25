import sqlite3

DB_PATH = "Users.db"

def create_entry(chat_id):
	conn = sqlite3.connect(DB_PATH)
	cursor = conn.cursor()
	cursor.execute("INSERT INTO users chatID", (chat_id,))
	conn.commit()
	conn.close()

def update_location(chat_id, lat, lon):
	conn = sqlite3.connect(DB_PATH)
	cursor = conn.cursor()
	cursor.execute("UPDATE users SET latitude = ? WHERE chatID = ?", (lat, chat_id))
	cursor.execute("UPDATE users SET longitude = ? WHERE chatID = ?", (lon, chat_id))
	conn.commit()
	conn.close()

def update_lang(chat_id, lang):
	conn = sqlite3.connect(DB_PATH)
	cursor = conn.cursor()
	cursor.execute("UPDATE users SET language = ? WHERE chatID = ?", (lang, chat_id))
	conn.commit()
	conn.close()

def view_users(chat_id):
	conn = sqlite3.connect(DB_PATH)
	cursor = conn.cursor()
	cursor.execute("SELECT chatID FROM users WHERE chatID = ?", (chat_id,))
	result = cursor.fetchone()
	conn.close()
	if result:
		return result
	else:
		return 0

def view_location(chat_id):
	conn = sqlite3.connect(DB_PATH)
	cursor = conn.cursor()
	cursor.execute("SELECT latitude, longitude FROM users WHERE chatID = ?", (chat_id,))
	result = cursor.fetchall()
	conn.close()
	return result

def view_lang(chat_id):
	conn = sqlite3.connect(DB_PATH)
	cursor = conn.cursor()
	cursor.execute("SELECT language FROM users WHERE chatID = ?", (chat_id,))
	result = cursor.fetchone()
	conn.close()
	return result[0]