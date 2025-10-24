import logging
import os
import httpx
import sqlite3
from typing import Union

class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self._table_name = None
    
    def _map_type(self, py_type: type) -> str:
        type_map = {
            int: "INTEGER",
            str: "TEXT",
            float: "REAL",
            bool: "INTEGER"
        }
        return type_map.get(py_type, "TEXT")

    def _table_exists(self, table_name: str) -> bool:
        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
            return cur.fetchone() is not None

    def _get_existing_columns(self, table_name: str) -> set[str]:
        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info({table_name});")
            return {row[1] for row in cur.fetchall()}  # row[1] is column name

    def create_default_table(self, table_name: str, **columns: type):
        """
        Create the table if not exists. If it exists, add any missing columns.
        Passing columns overwrites defaults (i.e. you supply exact columns you want).
        """

        if not columns:
            # If you want defaults when user omitted columns, uncomment:
            # columns = {"username": str, "user_id": int}
            raise ValueError("You must provide at least one column.")

        self._table_name = table_name  # remember last created (or used) table

        # Build column definitions for CREATE TABLE
        cols = []
        for name, py_type in columns.items():
            sqlite_type = self._map_type(py_type)
            cols.append(f"{name} {sqlite_type} UNIQUE")

        columns_def = ", ".join(cols)
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def});"

        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()
            cur.execute(create_sql)

        # If table already existed, make sure missing columns are added
        if self._table_exists(table_name):
            existing = self._get_existing_columns(table_name)
            # For each requested column not present, add it
            for name, py_type in columns.items():
                if name not in existing:
                    col_type = self._map_type(py_type)
                    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {name} {col_type};"
                    with sqlite3.connect(self.db_name) as conn:
                        conn.execute(alter_sql)
    
    def create_table(self, table_name: str, **columns: type):
        """
        Drops the table (if exists) and creates it with the given columns.
        WARNING: This destroys existing data in that table.
        """
        if not columns:
            raise ValueError("You must provide at least one column.")
        drop_sql = f"DROP TABLE IF EXISTS {table_name};"
        cols = []
        for name, py_type in columns.items():
            sqlite_type = self._map_type(py_type)
            cols.append(f"{name} {sqlite_type} UNIQUE")
        create_sql = f"CREATE TABLE {table_name} ({', '.join(cols)});"
        with sqlite3.connect(self.db_name) as conn:
            conn.execute(drop_sql)
            conn.execute(create_sql)
        self._table_name = table_name

    def add_data(self, table_name, **data):
        if not data:
            raise ValueError("You must provide at least one column and value.")

        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        values = tuple(data.values())

        query = f"INSERT OR IGNORE INTO {table_name} ({columns}) VALUES ({placeholders});"

        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()
            cur.execute(query, values)
    
    def get_data(self):
        if not self._table_name:
            raise ValueError("No table created yet.")
        with sqlite3.connect(self.db_name) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            return [dict(row) for row in cur.execute(f"SELECT * FROM {self._table_name}").fetchall()]

# Exception
class FileNotFoundOrInvalidURLError(Exception):
    """Raised when a file does not exist or the provided URL is invalid."""
    pass

# Buttons
def KeyboardButton(*rows: list[str], resize_keyboard: bool = True, one_time_keyborad: bool = False):
    return {
        "keyboard": list(rows),
        'resize_keyboard': resize_keyboard,
        'one_time_keyboard': one_time_keyborad
    }

def InlineKeyboardButton(*rows: list[list[str, str]]) -> dict[str, list]:
    keyboard = []
    for row in rows:
        keyboard_row = [{"text": text, "callback_data": data} for text, data in row]
        keyboard.append(keyboard_row)
    return {"inline_keyboard": keyboard}

def URLKeyboardButton(*rows: list[list[str, str]]) -> dict[str, list]:
    keyboard = []
    for row in rows:
        keyboard_row = [{"text": text, "url": data} for text, data in row]
        keyboard.append(keyboard_row)
    return {"inline_keyboard": keyboard}

def RemoveKeyboardButton():
    return {
        'remove_keyboard': True
    }


# For sendinng media and handling
class Photo:
    def __init__(self, url, caption=""):
        self.url = url
        self.caption = caption

class Video:
    def __init__(self, url, caption=""):
        self.url = url
        self.caption = caption

class Audio:
    def __init__(self, url, caption=""):
        self.url = url
        self.caption = caption

class Voice:
    def __init__(self, url, caption=""):
        self.url = url
        self.caption = caption

class Sticker:
    def __init__(self, file_id):
        self.file_id = file_id

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s", "%Y-%m-%d %H:%M:%S")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)

    return logger

# Bot
class Bot:
    def __init__(self, token, auto_db: bool = True, db_name: str = "database.db", admin_id: int = None):
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.handlers = {}
        self.callback_handlers = {}
        self.logger = setup_logger("osonbot")
        self.auto_db = auto_db
        self.admin_id = admin_id
        if auto_db:
            db = Database(db_name)
            self.db = db
            self.db.create_default_table("users", username=str, user_id=int)

    def when(self, condition: str | list[str], text: str, parse_mode: str = None, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None):
        if condition:
            if isinstance(condition, list):
                for cond in condition:
                    self.handlers[cond] = {"text": text, 'parse_mode': parse_mode, 'reply_markup': reply_markup}
            else:
                self.handlers[condition] = {"text": text, 'parse_mode': parse_mode, 'reply_markup': reply_markup}

    def c_when(self, condition: str | list[str], text: str, parse_mode: str = None, reply_markup: str = None):
        if condition:
            if isinstance(condition, list):
                for cond in condition:
                    self.callback_handlers[cond] = {"text": text, 'parse_mode': parse_mode, 'reply_markup': reply_markup}
            else:
                self.callback_handlers[condition] = {'text': text, "parse_mode": parse_mode, "reply_markup": reply_markup}

    def get_updates(self, offset: int):
        return httpx.get(self.api_url+"getUpdates", params={'offset': offset}).json()
    
    def send_message(self, chat_id, text: str, parse_mode: str = None, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None):
        params = {'chat_id': chat_id, "text": text}
        if parse_mode:
            params['parse_mode'] = parse_mode
        if reply_markup:
            params['reply_markup'] = reply_markup
        httpx.post(self.api_url+"sendMessage", json=params)
    
    def send_photo(self, chat_id, photo: str, caption: str = None, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None, parse_mode: str = None):
        try:
            if os.path.exists(photo):
                data = {"chat_id": chat_id, 'caption': caption}
                if reply_markup:
                    data['reply_markup'] = reply_markup
                if parse_mode:
                    data['parse_mode'] = parse_mode
                with open(photo, 'rb') as p:
                    httpx.post(self.api_url+"sendPhoto", data=data, files={"photo": p})
            elif "https://" in photo or "http://" in photo:
                json = {"chat_id": chat_id, "photo": photo, 'caption': caption}
                if reply_markup:
                    json['reply_markup'] = reply_markup
                if parse_mode:
                    json['parse_mode'] = parse_mode
                httpx.post(self.api_url+"sendPhoto", json=json)
            else:
                raise FileNotFoundOrInvalidURLError(f"Photo not found or invalid URL: {photo}")
        except:
            self.logger.error("Error occured: ", exc_info=True)

    def send_video(self, chat_id, video: str, caption, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None, parse_mode: str = None):
        try:
            if os.path.exists(video):
                data = {"chat_id": chat_id, 'caption': caption}
                if reply_markup:
                    data['reply_markup'] = reply_markup
                if parse_mode:
                    data['parse_mode'] = parse_mode
                with open(video, 'rb') as v:
                    httpx.post(self.api_url+"sendVideo", data=data, files={"video": v})
            elif "https://" in video or "http://" in video:
                json = {"chat_id": chat_id, "video": video, 'caption': caption}
                if reply_markup:
                    json['reply_markup'] = reply_markup
                if parse_mode:
                    json['parse_mode'] = parse_mode
                httpx.post(self.api_url+"sendVideo", json=json)
            else:
                raise FileNotFoundOrInvalidURLError(f"Video not found or invalid URL: {video}")
        except:
            self.logger.error("Error occured: ", exc_info=True)

    def send_audio(self, chat_id, audio: str, caption, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None, parse_mode: str = None):
        try:
            if os.path.exists(audio):
                data = {"chat_id": chat_id, 'caption': caption}
                if reply_markup:
                    data['reply_markup'] = reply_markup
                if parse_mode:
                    data['parse_mode'] = parse_mode
                with open(audio, 'rb') as a:
                    httpx.post(self.api_url+"sendAudio", data=data, files={"audio": a})
            elif "https://" in audio or "http://" in audio:
                json = {"chat_id": chat_id, "audio": audio, 'caption': caption, 'reply_markup': reply_markup}
                if reply_markup:
                    json['reply_markup'] = reply_markup
                if parse_mode:
                    json['parse_mode'] = parse_mode
                httpx.post(self.api_url+"sendAudio", json=json)
            else:
                raise FileNotFoundOrInvalidURLError(f"Audio not found or invalid URL: {audio}")
        except:
            self.logger.error("Error occured: ", exc_info=True)
    
    def send_voice(self, chat_id, voice: str, caption, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None, parse_mode: str = None):
        try:
            if os.path.exists(voice):
                data = {"chat_id": chat_id, 'caption': caption}
                if reply_markup:
                    data['reply_markup'] = reply_markup
                if parse_mode:
                    data['parse_mode'] = parse_mode
                with open(voice, 'rb') as v:
                    httpx.post(self.api_url+"sendVoice", data=data, files={"voice": v})
            else:
                raise FileNotFoundError(f"file {voice} not found. Make sure it exists")
        except:
            self.logger.error("Error occured: ", exc_info=True)
    
    def send_sticker(self, chat_id, sticker: str, reply_markup: dict = None):
        params = {"chat_id": chat_id, "sticker": sticker}
        if reply_markup:
            params['reply_markup'] = reply_markup
        httpx.post(self.api_url + "sendSticker", json=params)
    
    def formatter(self, text: str, message):
        try:
            return text.format(
                    first_name=message['from']['first_name'],
                    last_name=message['from']['last_name'],
                    full_name=f"{message['from']['first_name']} {message['from']['last_name']}",
                    message_text=message['text'],
                    user_id=message['from']['id'],
                    message_id=message['message_id']
                )
        except:
            try:
                return text.format(
                        first_name=message['chat']['first_name'] if 'first_name' in message['chat'] else "",
                        last_name=message['chat']['last_name'] if 'last_name' in message['chat'] else "",
                        full_name=f"{message['chat']['first_name'] if 'first_name' in message['chat'] else ''} {message['chat']['last_name'] if 'last_name' in message['chat'] else ''}",
                        message_text=message['text'],
                        user_id=message['from']['id'],
                        message_id=message['message_id']
                    )
            except:
                return text
    
    def get_me(self):
        return httpx.get(self.api_url + "getMe").json()

    def process_callback(self, callback):
        message = callback.get("message", {})
        data = callback.get('data')
        chat_id = message['chat']['id']
        handled = self.callback_handlers.get(data)
        
        if not handled:
            return

        self.send_message(chat_id, self.formatter(handled['text'], message))
    
    def process_messages(self, message):
        chat_id = message['from']['id']

        if self.auto_db:
            self.db.add_data("users", username=message['from']['username'], user_id=chat_id)

        if "text" in message:
            text = message.get("text", "")
            chat_id = message['chat']['id']
            handled = self.handlers.get(text) or self.handlers.get("*")

            if not handled:
                return
            
            if callable(handled['text']):
                returned = handled['text'](message)
                if isinstance(returned, Photo):
                    self.send_photo(chat_id, returned.url, caption=self.formatter(returned.caption, message), reply_markup=handled['reply_markup'], parse_mode=handled['parse_mode'])
                elif isinstance(returned, Video):
                    self.send_video(chat_id, returned.url, caption=self.formatter(returned.caption, message), reply_markup=handled['reply_markup'], parse_mode=handled['parse_mode'])
                elif isinstance(returned, Audio):
                    self.send_audio(chat_id, returned.url, caption=self.formatter(returned.caption, message), reply_markup=handled['reply_markup'], parse_mode=handled['parse_mode'])
                elif isinstance(returned, Voice):
                    self.send_voice(chat_id, returned.url, caption=self.formatter(returned.caption, message), reply_markup=handled['reply_markup'], parse_mode=handled['parse_mode'])
                elif isinstance(returned, Sticker):
                    self.send_sticker(chat_id, returned.file_id, reply_markup=handled['reply_markup'])
                elif isinstance(returned, str):
                    self.send_message(chat_id, self.formatter(returned, message), parse_mode=handled['parse_mode'], reply_markup=handled['reply_markup'])
            
            if isinstance(handled['text'], Photo):
                self.send_photo(chat_id, self.formatter(handled['text'].url, message), caption=self.formatter(handled['text'].caption, message), reply_markup=handled['reply_markup'], parse_mode=handled['parse_mode'])
            elif isinstance(handled['text'], Video):
                self.send_video(chat_id, self.formatter(handled['text'].url, message), caption=self.formatter(handled['text'].caption, message), reply_markup=handled['reply_markup'], parse_mode=handled['parse_mode'])
            elif isinstance(handled['text'], Audio):
                self.send_audio(chat_id, self.formatter(handled['text'].url, message), caption=self.formatter(handled['text'].caption, message), reply_markup=handled['reply_markup'], parse_mode=handled['parse_mode'])
            elif isinstance(handled['text'], Voice):
                self.send_voice(chat_id, self.formatter(handled['text'].url, message), caption=self.formatter(handled['text'].caption, message), reply_markup=handled['reply_markup'], parse_mode=handled['parse_mode'])
            elif isinstance(handled['text'], Sticker):
                self.send_sticker(chat_id, handled['text'].file_id, reply_markup=handled['reply_markup'])
            elif isinstance(handled['text'], str):
                self.send_message(chat_id, self.formatter(handled['text'], message), parse_mode=handled['parse_mode'], reply_markup=handled['reply_markup'])
        elif "photo" in message:
            hv = self.handlers.get(Photo)
            self.send_message(chat_id, hv['text'], parse_mode=hv['parse_mode'], reply_markup=hv['reply_markup'])
        elif "video" in message:
            hv = self.handlers.get(Video)
            self.send_message(chat_id, hv['text'], parse_mode=hv['parse_mode'], reply_markup=hv['reply_markup'])
        elif "sticker" in message:
            hv = self.handlers.get(Sticker)
            self.send_message(chat_id, hv['text'], parse_mode=hv['parse_mode'], reply_markup=hv['reply_markup'])
        
    def admin_handler(self, message):
        if not self.admin_id:
            self.logger.error("Admin id is not set", exc_info=True)
        
        if message['from']['id'] == self.admin_id:
            return "Welcome Admin!"
        else:
            return "/admin"
    
    def run(self):
        getme = self.get_me()
        self.logger.info(f"[@{getme['result']['username']} - id={getme['result']['id']}] successfully started")
        offset = 0
        while True:
            try:
                for update in self.get_updates(offset).get("result", []):
                    offset = update['update_id'] + 1

                    self.when("/admin", self.admin_handler, reply_markup=KeyboardButton())

                    if "callback_query" in update:
                        self.process_callback(update['callback_query'])
                    elif "message" in update:
                        self.process_messages(update['message'])
                    
            except Exception as e:
                self.logger.error("Error occured", exc_info=True)
