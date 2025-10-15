import os
import httpx


class FileNotFoundOrInvalidURLError(Exception):
    """Raised when a file does not exist or the provided URL is invalid."""
    pass

class NotInstanceError(Exception):
    pass


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


class Bot:
    def __init__(self, token):
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.handlers = {}

    def when(self, condition: str, text: str, parse_mode: str = None, reply_markup: str = None):
        if condition:
            self.handlers[condition] = {"text": text, 'parse_mode': parse_mode, 'reply_markup': reply_markup}
    
    def get_updates(self, offset: int):
        return httpx.get(self.api_url+"getUpdates", params={'offset': offset}).json()
    
    def send_message(self, chat_id, text: str, parse_mode: str = None, reply_markup: list[list[str]] = None):
        params = {'chat_id': chat_id, "text": text, 'reply_markup': reply_markup}
        if parse_mode:
            params['parse_mode'] = parse_mode
        httpx.post(self.api_url+"sendMessage", json=params)
    
    def send_photo(self, chat_id, photo: str, caption, reply_markup: list[list[str]] = None):
        try:
            if os.path.exists(photo):
                with open(photo, 'rb') as p:
                    httpx.post(self.api_url+"sendPhoto", data={"chat_id": chat_id, 'caption': caption, 'reply_markup': reply_markup}, files={"photo": p})
            elif "https://" in photo:
                httpx.post(self.api_url+"sendPhoto", json={"chat_id": chat_id, "photo": photo, 'caption': caption, 'reply_markup': reply_markup})
        except:
            raise FileNotFoundOrInvalidURLError(f"Photo not found or invalid URL: {photo}")

    def send_video(self, chat_id, video: str, caption, reply_markup: list[list[str]] = None):
        try:
            if os.path.exists(video):
                with open(video, 'rb') as v:
                    httpx.post(self.api_url+"sendVideo", data={"chat_id": chat_id, 'caption': caption, 'reply_markup': reply_markup}, files={"video": v})
            elif "https://" in video:
                httpx.post(self.api_url+"sendVideo", json={"chat_id": chat_id, "video": video, 'caption': caption, 'reply_markup': reply_markup})
        except:
            raise FileNotFoundOrInvalidURLError(f"Video not found or invalid URL: {video}")

    def send_audio(self, chat_id, audio: str, caption, reply_markup: list[list[str]] = None):
        try:
            if os.path.exists(audio):
                with open(audio, 'rb') as a:
                    httpx.post(self.api_url+"sendAudio", data={"chat_id": chat_id, 'caption': caption, 'reply_markup': reply_markup}, files={"audio": a})
            elif "https://" in audio:
                httpx.post(self.api_url+"sendAudio", json={"chat_id": chat_id, "audio": audio, 'caption': caption, 'reply_markup': reply_markup})
        except:
            raise FileNotFoundOrInvalidURLError(f"Audio not found or invalid URL: {audio}")
    
    def send_voice(self, chat_id, voice: str, caption, reply_markup: list[list[str]] = None):
        try:
            if os.path.exists(voice):
                with open(voice, 'rb') as v:
                    httpx.post(self.api_url+"sendVoice", data={"chat_id": chat_id, 'caption': caption, 'reply_markup': reply_markup}, files={"voice": v})
        except:
            raise FileNotFoundOrInvalidURLError(f"Audio not found or invalid URL: {voice}")

    def process_messages(self, message):
        text = message.get("text", "")
        chat_id = message['chat']['id']
        handled = self.handlers.get(text) or self.handlers.get("*")
        
        if isinstance(handled['text'], Photo):
            self.send_photo(chat_id, handled['text'].url, caption=handled['text'].caption, reply_markup=handled['reply_markup'])
        elif isinstance(handled['text'], Video):
            self.send_video(chat_id, handled['text'].url, caption=handled['text'].caption, reply_markup=handled['reply_markup'])
        elif isinstance(handled['text'], Audio):
            self.send_audio(chat_id, handled['text'].url, caption=handled['text'].caption, reply_markup=handled['reply_markup'])
        elif isinstance(handled['text'], Voice):
            self.send_voice(chat_id, handled['text'].url, handled['text'].caption, reply_markup=handled['reply_markup'])
        elif isinstance(handled['text'], str):
            self.send_message(chat_id, handled['text'].format(
                first_name=message['from']['first_name'],
                last_name=message['from']['last_name'],
                full_name=f"{message['from']['first_name']} {message['from']['last_name']}",
                message_text=message['text'],
                user_id=message['from']['id'],
                message_id=message['message_id']
            ), parse_mode=handled['parse_mode'], reply_markup=handled['reply_markup'])
    
    def run(self):
        offset = 0
        while True:
            try:
                for update in self.get_updates(offset).get("result", []):
                    offset = update['update_id'] + 1
                    message = update.get("message")
                    if not message:
                        continue

                    self.process_messages(message)
                    
            except Exception as e:
                print("Error occured: ", e)
                print(e.with_traceback(None))


def KeyboardButton(*rows, resize_keyboard: bool = True, one_time_keyborad: bool = False):
    return {
        "keyboard": list(rows),
        'resize_keyboard': resize_keyboard,
        'one_time_keyboard': one_time_keyborad
    }
