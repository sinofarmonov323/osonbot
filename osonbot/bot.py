import os
import httpx
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class Video:
    def __init__(self, url, caption=None):
        self.url = url
        self.caption = caption

class Photo:
    def __init__(self, url, caption=None):
        self.url = url
        self.caption = caption

class Audio:
    def __init__(self, url, caption=None):
        self.url = url
        self.caption = caption

class Bot:
    def __init__(self, token: str):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.handlers = {}
        self.user_context = {}
        self._current_id = None

    def when(self, condition, text, reply_markup=None, once: bool = False):
        """
        Register a handler for a specific condition (command, message, media type, or '*').
        You can include a `reply_markup` dict for buttons.
        
        condition can be:
        - A string like "/start" or "*"
        - A media class like Photo, Video, Audio
        """
        if not condition:
            logger.error("No condition provided.")
            return self
        self.handlers[condition] = {
            "text": text,
            "reply_markup": reply_markup,
            "once": once,
        }
        return self

    def _send_message(self, chat_id: int, text: str, reply_markup=None):
        """Send a text message."""
        payload = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        httpx.post(f"{self.api_url}sendMessage", json=payload)

    def _get_updates(self, offset=None):
        """Fetch new updates."""
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset
        try:
            response = httpx.get(f"{self.api_url}getUpdates", params=params, timeout=40)
            return response.json()
        except httpx.ReadTimeout:
            return {"result": []}

    def get_me(self):
        return httpx.get(f"{self.api_url}getMe").json().get("result", {})
    
    def send_photo(self, chat_id, photo_url_or_path: str, caption=None, reply_markup=None):
        """Send a photo from either a URL or local file path."""
        if os.path.exists(photo_url_or_path):
            with open(photo_url_or_path, "rb") as photo:
                files = {"photo": photo}
                data = {"chat_id": chat_id, "caption": caption or ""}
                if reply_markup:
                    data["reply_markup"] = reply_markup
                httpx.post(f"{self.api_url}sendPhoto", data=data, files=files)
        else:
            payload = {"chat_id": chat_id, "photo": photo_url_or_path, "caption": caption or ""}
            if reply_markup:
                payload["reply_markup"] = reply_markup
            httpx.post(f"{self.api_url}sendPhoto", json=payload)

    def send_video(self, chat_id, video_url_or_path: str, caption=None, reply_markup=None):
        """Send a video from either a URL or local file path."""
        if os.path.exists(video_url_or_path):
            with open(video_url_or_path, "rb") as video:
                files = {"video": video}
                data = {"chat_id": chat_id, "caption": caption or ""}
                if reply_markup:
                    data["reply_markup"] = reply_markup
                httpx.post(f"{self.api_url}sendVideo", data=data, files=files)
        else:
            payload = {"chat_id": chat_id, "video": video_url_or_path, "caption": caption or ""}
            if reply_markup:
                payload["reply_markup"] = reply_markup
            httpx.post(f"{self.api_url}sendVideo", json=payload)

    def send_audio(self, chat_id, audio_url_or_path: str, caption=None, reply_markup=None):
        """Send audio from either a URL or local file path."""
        if os.path.exists(audio_url_or_path):
            with open(audio_url_or_path, "rb") as audio:
                files = {"audio": audio}
                data = {"chat_id": chat_id, "caption": caption or ""}
                if reply_markup:
                    data["reply_markup"] = reply_markup
                httpx.post(f"{self.api_url}sendAudio", data=data, files=files)
        else:
            payload = {"chat_id": chat_id, "audio": audio_url_or_path, "caption": caption or ""}
            if reply_markup:
                payload["reply_markup"] = reply_markup
            httpx.post(f"{self.api_url}sendAudio", json=payload)
    
    def send_voice(self, chat_id, voice_path, caption=None):
        """🎤 Sends a voice message (.ogg or .mp3) from storage"""
        with open(voice_path, "rb") as voice:
            httpx.post(self.api_url + "sendVoice", data={"chat_id": chat_id, "caption": caption}, files={"voice": voice})

    def _build_format_context(self, message):
        user = message.get("from", {})
        return {
            "id": user.get("id"),
            "user": user,
            "first_name": user.get("first_name", ""),
            "full_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "last_name": user.get("last_name", ""),
            "username": user.get("username", ""),
            "message_text": message.get("text", ""),
            "message": message,
        }

    def _get_media_type(self, message):
        """Determine what type of media is in the message."""
        if message.get("photo"):
            return Photo
        elif message.get("video"):
            return Video
        elif message.get("audio"):
            return Audio
        return None

    def run(self):
        """Start the bot and handle incoming messages."""
        offset = 0
        me = self.get_me()
        logger.info(f"@{me.get('username', 'bot')} is running...")

        while True:
            try:
                data = self._get_updates(offset)
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    message = update.get("message")
                    if not message:
                        continue

                    chat_id = message["chat"]["id"]
                    text = message.get("text", "")
                    user_id = message["from"]["id"]
                    self._current_id = user_id
                    self.user_context[user_id] = message

                    media_type = self._get_media_type(message)
                    handler_entry = None
                    
                    if text and text in self.handlers:
                        handler_entry = self.handlers.get(text)
                    elif media_type and media_type in self.handlers:
                        handler_entry = self.handlers.get(media_type)
                    else:
                        handler_entry = self.handlers.get("*")
                    
                    if not handler_entry:
                        continue
                    
                    handler = handler_entry["text"]
                    reply_markup = handler_entry.get("reply_markup")
                    ctx = self._build_format_context(message)

                    if callable(handler):
                        try:
                            reply = handler(message)
                        except Exception as e:
                            logger.error(f"Handler error: {e}")
                            reply = "An error occurred."
                    else:
                        try:
                            reply = handler.format(**ctx)
                        except Exception:
                            reply = handler

                    if isinstance(handler, Photo):
                        self.send_photo(chat_id, handler.url, reply_markup=reply_markup, caption=handler.caption)
                        reply = None
                    elif isinstance(handler, Video):
                        self.send_video(chat_id, handler.url, reply_markup=reply_markup, caption=handler.caption)
                        reply = None
                    elif isinstance(handler, Audio):
                        self.send_audio(chat_id, handler.url, reply_markup=reply_markup, caption=handler.caption)
                        reply = None

                    if reply:
                        self._send_message(chat_id, reply, reply_markup=reply_markup)

                    if handler_entry.get("once"):
                        if text and text in self.handlers:
                            del self.handlers[text]
                        elif media_type and media_type in self.handlers:
                            del self.handlers[media_type]

            except Exception as e:
                logger.error(f"Error: {e}")

def KeyboardButton(*rows, resize_keyboard=True, one_time_keyboard=False):
    return {
        "keyboard": [[{"text": btn} for btn in row] for row in rows],
        "resize_keyboard": resize_keyboard,
        "one_time_keyboard": one_time_keyboard,
    }


def InlineKeyboardButton(*rows):
    return {
        "inline_keyboard": [
            [{"text": text, "callback_data": callback} for text, callback in row]
            for row in rows
        ]
    }


def URLKeyboardButton(*rows):
    return {
        "inline_keyboard": [
            [{"text": text, "url": url} for text, url in row] for row in rows
        ]
    }

def RemoveKeyboardButton(selective=False):
    """Hides the custom keyboard and shows the default Telegram input."""
    return {
        "remove_keyboard": True,
        "selective": selective,
    }
