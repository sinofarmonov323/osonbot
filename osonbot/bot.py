import os
import httpx
from typing import Union, Callable, Optional
from .database import Database
from .utils import (
    FileNotFoundOrInvalidURLError, 
    Photo, Video, Audio, Voice, Document, Sticker,
    setup_logger, 
    InlineKeyboardButton, RemoveKeyboardButton, URLKeyboardButton, KeyboardButton,
    Message
)


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
        return httpx.post(self.api_url+"sendMessage", json=params).json()['result']
    
    def send_photo(self, chat_id, photo: str, caption: str = None, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None, parse_mode: str = None):
        try:
            if os.path.exists(photo):
                data = {"chat_id": chat_id, 'caption': caption}
                if reply_markup:
                    data['reply_markup'] = reply_markup
                if parse_mode:
                    data['parse_mode'] = parse_mode
                with open(photo, 'rb') as p:
                    return httpx.post(self.api_url+"sendPhoto", data=data, files={"photo": p}).json()
            elif "https://" in photo or "http://" in photo:
                json = {"chat_id": chat_id, "photo": photo, 'caption': caption}
                if reply_markup:
                    json['reply_markup'] = reply_markup
                if parse_mode:
                    json['parse_mode'] = parse_mode
                return httpx.post(self.api_url+"sendPhoto", json=json).json()
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
                    return httpx.post(self.api_url+"sendVideo", data=data, files={"video": v}).json()['result']
            elif "https://" in video or "http://" in video:
                json = {"chat_id": chat_id, "video": video, 'caption': caption}
                if reply_markup:
                    json['reply_markup'] = reply_markup
                if parse_mode:
                    json['parse_mode'] = parse_mode
                return httpx.post(self.api_url+"sendVideo", json=json).json()['result']
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
                    return httpx.post(self.api_url+"sendAudio", data=data, files={"audio": a}).json()['result']
            elif "https://" in audio or "http://" in audio:
                json = {"chat_id": chat_id, "audio": audio, 'caption': caption, 'reply_markup': reply_markup}
                if reply_markup:
                    json['reply_markup'] = reply_markup
                if parse_mode:
                    json['parse_mode'] = parse_mode
                return httpx.post(self.api_url+"sendAudio", json=json).json()['result']
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
                    return httpx.post(self.api_url+"sendVoice", data=data, files={"voice": v}).json()['result']
            else:
                raise FileNotFoundError(f"file {voice} not found. Make sure it exists")
        except:
            self.logger.error("Error occured: ", exc_info=True)
    
    def send_sticker(self, chat_id, sticker: str, reply_markup: dict = None):
        params = {"chat_id": chat_id, "sticker": sticker}
        if reply_markup:
            params['reply_markup'] = reply_markup
        return httpx.post(self.api_url + "sendSticker", json=params).json()['result']
    
    def send_document(self, chat_id, document: str, caption: str = None, parse_mode: str = None, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None):
        try:
            if os.path.exists(document):
                data = {"chat_id": chat_id, 'caption': caption}
                if reply_markup:
                    data['reply_markup'] = reply_markup
                if parse_mode:
                    data['parse_mode'] = parse_mode
                with open(document, 'rb') as v:
                    return httpx.post(self.api_url+"senddocument", data=data, files={"document": v}).json()['result']
            elif "https://" in document or "http://" in document:
                json = {"chat_id": chat_id, "document": document, 'caption': caption}
                if reply_markup:
                    json['reply_markup'] = reply_markup
                if parse_mode:
                    json['parse_mode'] = parse_mode
                return httpx.post(self.api_url+"senddocument", json=json).json()['result']
            else:
                raise FileNotFoundOrInvalidURLError(f"document not found or invalid URL: {document}")
        except:
            self.logger.error("Error occured: ", exc_info=True)

    def edit_message_text(self, chat_id: int, message_id: int, text: str, parse_mode: str = None, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None):
        params = {'chat_id': chat_id, 'message_id': message_id, 'text': text}
        if parse_mode:
            params['parse_mode'] = parse_mode
        if reply_markup:
            params['reply_markup'] = reply_markup
        return httpx.post(self.api_url + "editMessageText", json=params).json()['result']
    
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

        if self.admin_id:
            if message['from']['id'] == self.admin_id:
                self.when("/admin", "Welcome Admin!", reply_markup=KeyboardButton(['statistika📊']))
                self.when("statistika📊", f"Foydalanuvchilar soni: {len(self.db.get_data())}")

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
                elif isinstance(returned, Document):
                    self.send_document(chat_id, returned.file_id, caption=self.formatter(returned.caption, message), reply_markup=handled['reply_markup'], parse_mode=handled['parse_mode'])
            
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
            elif isinstance(returned, Document):
                self.send_document(chat_id, returned.file_id, caption=self.formatter(returned.caption, message), reply_markup=handled['reply_markup'], parse_mode=handled['parse_mode'])
        
        elif "photo" in message:
            hv = self.handlers.get(Photo)
            self.send_message(chat_id, hv['text'], parse_mode=hv['parse_mode'], reply_markup=hv['reply_markup'])
        elif "video" in message:
            hv = self.handlers.get(Video)
            self.send_message(chat_id, hv['text'], parse_mode=hv['parse_mode'], reply_markup=hv['reply_markup'])
        elif "sticker" in message:
            hv = self.handlers.get(Sticker)
            self.send_message(chat_id, hv['text'], parse_mode=hv['parse_mode'], reply_markup=hv['reply_markup'])
        elif "document" in message:
            hv = self.handlers.get(Document)
            self.send_message(chat_id, hv['text'], parse_mode=hv['parse_mode'], reply_markup=hv['reply_markup'])
    
    def run(self):
        getme = self.get_me()
        try:
            self.logger.info(f"[@{getme['result']['username']} - id={getme['result']['id']}] successfully started")
        except:
            raise Exception(f"No telegram bot found based on the token")
        offset = 0
        while True:
            try:
                for update in self.get_updates(offset).get("result", []):
                    offset = update['update_id'] + 1

                    if "callback_query" in update:
                        self.process_callback(update['callback_query'])
                    elif "message" in update:
                        self.process_messages(update['message'])
                    
            except Exception as e:
                self.logger.error("Error occured", exc_info=True)
