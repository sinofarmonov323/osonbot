import logging
import os
import httpx

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

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s", "%Y-%m-%d %H:%M:%S")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)

    return logger

logger = setup_logger("osonbot")

# Bot
class Bot:
    def __init__(self, token):
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.handlers = {}
        self.callback_handlers = {}

    def when(self, condition: str | list[str], text: str, parse_mode: str = None, reply_markup: str = None):
        if isinstance(condition, str):
            self.handlers[condition] = {"text": text, 'parse_mode': parse_mode, 'reply_markup': reply_markup}
        elif isinstance(condition, list):
            for cond in condition:
                self.handlers[cond] = {"text": text, 'parse_mode': parse_mode, 'reply_markup': reply_markup}
    
    def c_when(self, condition: str | list[str], text: str, parse_mode: str = None, reply_markup: str = None):
        if isinstance(condition, str):
            self.callback_handlers[condition] = {'text': text, "parse_mode": parse_mode, "reply_markup": reply_markup}
        elif isinstance(condition, list):
            for cond in condition:
                self.callback_handlers[cond] = {"text": text, 'parse_mode': parse_mode, 'reply_markup': reply_markup}
    
    def get_updates(self, offset: int):
        return httpx.get(self.api_url+"getUpdates", params={'offset': offset}).json()
    
    def send_message(self, chat_id, text: str, parse_mode: str = None, reply_markup: list[list[str]] = None):
        params = {'chat_id': chat_id, "text": text}
        if parse_mode:
            params['parse_mode'] = parse_mode
        if reply_markup:
            params['reply_markup'] = reply_markup
        httpx.post(self.api_url+"sendMessage", json=params)
    
    def send_photo(self, chat_id, photo: str, caption, reply_markup: list[list[str]] = None):
        # try:
            if os.path.exists(photo):
                data = {"chat_id": chat_id, 'caption': caption}
                if reply_markup:
                    data['reply_markup'] = reply_markup
                with open(photo, 'rb') as p:
                    httpx.post(self.api_url+"sendPhoto", data=data, files={"photo": p})
            elif "https://" in photo or "http://" in photo:
                json = {"chat_id": chat_id, "photo": photo, 'caption': caption}
                if reply_markup:
                    json['reply_markup'] = reply_markup
                httpx.post(self.api_url+"sendPhoto", json=json)
            else:
                raise FileNotFoundOrInvalidURLError(f"Photo not found or invalid URL: {photo}")
        # except:
            # raise FileNotFoundOrInvalidURLError(f"Photo not found or invalid URL: {photo}")

    def send_video(self, chat_id, video: str, caption, reply_markup: list[list[str]] = None):
        # try:
            if os.path.exists(video):
                data = {"chat_id": chat_id, 'caption': caption}
                if reply_markup:
                    data['reply_markup'] = reply_markup
                with open(video, 'rb') as v:
                    httpx.post(self.api_url+"sendVideo", data=data, files={"video": v})
            elif "https://" in video or "http://" in video:
                json = {"chat_id": chat_id, "video": video, 'caption': caption}
                if reply_markup:
                    json['reply_markup'] = reply_markup
                httpx.post(self.api_url+"sendVideo", json=json)
            else:
                raise FileNotFoundOrInvalidURLError(f"Video not found or invalid URL: {video}")
        # except:
            # raise FileNotFoundOrInvalidURLError(f"Video not found or invalid URL: {video}")

    def send_audio(self, chat_id, audio: str, caption, reply_markup: list[list[str]] = None):
        # try:
            if os.path.exists(audio):
                data = {"chat_id": chat_id, 'caption': caption}
                if reply_markup:
                    data['reply_markup'] = reply_markup
                with open(audio, 'rb') as a:
                    httpx.post(self.api_url+"sendAudio", data=data, files={"audio": a})
            elif "https://" in audio or "http://" in audio:
                json = {"chat_id": chat_id, "audio": audio, 'caption': caption, 'reply_markup': reply_markup}
                if reply_markup:
                    json['reply_markup'] = reply_markup
                httpx.post(self.api_url+"sendAudio", json=json)
            else:
                raise FileNotFoundOrInvalidURLError(f"Audio not found or invalid URL: {audio}")
        # except:
            # raise FileNotFoundOrInvalidURLError(f"Audio not found or invalid URL: {audio}")
    
    def send_voice(self, chat_id, voice: str, caption, reply_markup: list[list[str]] = None):
        # try:
            if os.path.exists(voice):
                data = {"chat_id": chat_id, 'caption': caption}
                if reply_markup:
                    data['reply_markup'] = reply_markup
                with open(voice, 'rb') as v:
                    httpx.post(self.api_url+"sendVoice", data=data, files={"voice": v})
            else:
                raise FileNotFoundError(f"file {voice} not found. Make sure it exists")
        # except:
        #     raise FileNotFoundOrInvalidURLError(f"Audio not found or invalid URL: {voice}")
    
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

    def process_callback(self, callback):
        message = callback.get("message", {})
        data = callback.get('data')
        chat_id = message['chat']['id']
        handled = self.callback_handlers.get(data)
        
        if not handled:
            return

        self.send_message(chat_id, self.formatter(handled['text'], message))
    
    def process_messages(self, message):
        text = message.get("text", "")
        chat_id = message['chat']['id']
        handled = self.handlers.get(text) or self.handlers.get("*")
        
        if not handled:
            return

        hv = handled['text']

        if callable(hv):
            hv(message)
            return

        if isinstance(handled['text'], Photo):
            self.send_photo(chat_id, handled['text'].url, caption=self.formatter(handled['text'].caption, message), reply_markup=handled['reply_markup'])
        elif isinstance(handled['text'], Video):
            self.send_video(chat_id, handled['text'].url, caption=self.formatter(handled['text'].caption, message), reply_markup=handled['reply_markup'])
        elif isinstance(handled['text'], Audio):
            self.send_audio(chat_id, handled['text'].url, caption=self.formatter(handled['text'].caption, message), reply_markup=handled['reply_markup'])
        elif isinstance(handled['text'], Voice):
            self.send_voice(chat_id, handled['text'].url, caption=self.formatter(handled['text'].caption, message), reply_markup=handled['reply_markup'])
        elif isinstance(handled['text'], str):
            self.send_message(chat_id, self.formatter(handled['text'], message), parse_mode=handled['parse_mode'], reply_markup=handled['reply_markup'])
    
    def run(self):
        logger.info("Bot successfully started")
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
                logger.error("Error occured", exc_info=True)

def KeyboardButton(*rows: list[str], resize_keyboard: bool = True, one_time_keyborad: bool = False):
    return {
        "keyboard": list(rows),
        'resize_keyboard': resize_keyboard,
        'one_time_keyboard': one_time_keyborad
    }

def InlineKeyboardButton(*rows: list[list[str, str]]):
    keyboard = []
    for row in rows:
        keyboard_row = [{"text": text, "callback_data": data} for text, data in row]
        keyboard.append(keyboard_row)
    return {"inline_keyboard": keyboard}

def URLKeyboardButton(*rows: list[list[dict]]):
    keyboard = []
    for row in rows:
        keyboard_row = [{"text": text, "url": data} for text, data in row]
        keyboard.append(keyboard_row)
    return {"inline_keyboard": keyboard}

def RemoveKeyboardButton():
    return {
        'remove_keyboard': True
    }
