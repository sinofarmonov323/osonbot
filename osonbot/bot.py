import logging
import os
import httpx
import sqlite3

def create_table(table_name: str, **columns):
    if not columns:
        raise ValueError("You must provide at least one column.")

    type_map = {
        int: "INTEGER",
        str: "TEXT",
        float: "REAL",
        bool: "INTEGER"
    }

    cols = []
    for name, py_type in columns.items():
        sqlite_type = type_map.get(py_type, "TEXT")
        cols.append(f"{name} {sqlite_type} UNIQUE")

    columns_def = ", ".join(cols)
    query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def});"

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(query)

# def add_data(table_name: str, username: str, user_id: int):
#     with sqlite3.connect("database.db") as con:
#         cur = con.cursor()
#         cur.execute(f"INSERT OR IGNORE INTO {table_name} ()")

def add_data(table_name, **data):
    if not data:
        raise ValueError("You must provide at least one column and value.")

    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    values = tuple(data.values())

    query = f"INSERT OR IGNORE INTO {table_name} ({columns}) VALUES ({placeholders});"

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(query, values)

# Exception
class FileNotFoundOrInvalidURLError(Exception):
    """Raised when a file does not exist or the provided URL is invalid."""
    pass


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
    def __init__(self, token, admin_id=None, create_db=True):
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.handlers = {}
        self.callback_handlers = {}
        self.logger = setup_logger("osonbot")
        self.create_db = create_db
        self.admin_id = admin_id
        if create_db:
            create_table("users", username=str, user_id=int)
    
    def when(self, condition: str | list[str], text: str, parse_mode: str = None, reply_markup: KeyboardButton = None):
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
    
    def send_message(self, chat_id, text: str, parse_mode: str = None, reply_markup: list[list[str]] = None):
        params = {'chat_id': chat_id, "text": text}
        if parse_mode:
            params['parse_mode'] = parse_mode
        if reply_markup:
            params['reply_markup'] = reply_markup
        httpx.post(self.api_url+"sendMessage", json=params)
    
    def send_photo(self, chat_id, photo: str, caption: str = None, reply_markup: list[list[str]] = None, parse_mode: str = None):
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

    def send_video(self, chat_id, video: str, caption, reply_markup: list[list[str]] = None, parse_mode: str = None):
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

    def send_audio(self, chat_id, audio: str, caption, reply_markup: list[list[str]] = None, parse_mode: str = None):
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
    
    def send_voice(self, chat_id, voice: str, caption, reply_markup: list[list[str]] = None, parse_mode: str = None):
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
            return text.format(
                    first_name=message['chat']['first_name'],
                    last_name=message['chat']['last_name'],
                    full_name=f"{message['chat']['first_name']} {message['chat']['last_name']}",
                    message_text=message['text'],
                    user_id=message['from']['id'],
                    message_id=message['message_id']
                )
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

        if self.create_db:
            add_data("users", username=message['from']['username'], user_id=chat_id)

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

                    self.when("/admin", self.admin_handler, reply_markup='')

                    if "callback_query" in update:
                        self.process_callback(update['callback_query'])
                    elif "message" in update:
                        self.process_messages(update['message'])
                    
            except Exception as e:
                self.logger.error("Error occured", exc_info=True)

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
