import sqlite3

DB_PATH = "Users.db"

def create_entry(chat_id, lat, lon, lang):
	conn = sqlite3.connect(DB_PATH)
	cursor = conn.cursor()
	cursor.execute("INSERT INTO users (chatID, latitude, longitude, language) VALUES(?, ?, ?, ?)", (chat_id, lat, lon, lang))
	conn.commit()
	conn.close()

def update_location(chat_id, lat, lon):
	conn = sqlite3.connect(DB_PATH)
	cursor = conn.cursor()
	cursor.execute("UPDATE users SET (latitude = lat, longitude = lon) WHERE chatID = chat_id")
	conn.commit()
	conn.close()

def view_users(chat_id):
	conn = sqlite3.connect(DB_PATH)
	cursor = conn.cursor()
	cursor.execute("SELECT chatID FROM users WHERE chatID = ?", (chat_id))
	result = cursor.fetchone()
	conn.close()
	if result:
		return result
	else:
		return 0