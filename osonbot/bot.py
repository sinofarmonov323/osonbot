import os
import httpx
from typing import Union, Callable, Optional
from .database import Database
from .utils import (
    FileNotFoundOrInvalidURLError, 
    KeyboardButton, 
    Photo, 
    Video, 
    Audio, 
    Voice, 
    Document, 
    Sticker, 
    setup_logger, 
    Message, User, Chat
)


class Bot:
    def __init__(self, token: str, auto_db: bool = True, db_name: str = "database.db", admin_id: Optional[int] = None):
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.handlers = {}
        self.callback_handlers = {}
        self.logger = setup_logger("osonbot")
        self.auto_db = auto_db
        self.admin_id = admin_id
        
        if auto_db:
            self.db = Database(db_name)
            self.db.create_default_table("users", username=str, user_id=int)

    def when(self, condition: Union[str, list[str]], text: Union[str, Callable], parse_mode: Optional[str] = None, reply_markup: Optional[dict] = None):
        conditions = condition if isinstance(condition, list) else [condition]
        handler_data = {
            "text": text, 
            "parse_mode": parse_mode, 
            "reply_markup": reply_markup
        }
        
        for cond in conditions:
            self.handlers[cond] = handler_data
        
        return self

    def c_when(self, condition: Union[str, list[str]], text: Union[str, Callable], parse_mode: Optional[str] = None, reply_markup: Optional[dict] = None):
        conditions = condition if isinstance(condition, list) else [condition]
        handler_data = {
            "text": text, 
            "parse_mode": parse_mode, 
            "reply_markup": reply_markup
        }
        
        for cond in conditions:
            self.callback_handlers[cond] = handler_data
        
        return self

    def get_updates(self, offset: int) -> dict:
        try:
            response = httpx.get(
                self.api_url + "getUpdates", 
                params={"offset": offset},
                timeout=30.0
            )
            return response.json()
        except httpx.TimeoutException:
            self.logger.warning("Request timeout while getting updates")
            return {"result": []}
        except httpx.ConnectError:
            self.logger.error("Connection error. Check your internet connection")
            return {"result": []}

    def send_message(self, chat_id: int, text: str, parse_mode: Optional[str] = None, reply_markup: Optional[dict] = None) -> dict:
        params = {"chat_id": chat_id, "text": text}
        
        if parse_mode:
            params["parse_mode"] = parse_mode
        if reply_markup:
            params["reply_markup"] = reply_markup
        
        try:
            response = httpx.post(self.api_url + "sendMessage", json=params, timeout=30.0)
            data = response.json()
            return data.get("result", data)
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            self.logger.error(f"Error sending message: {e}")
            return {}

    def _send_file(self, method: str, chat_id: int, file_path: str, file_param: str, caption: Optional[str] = None, reply_markup: Optional[dict] = None, parse_mode: Optional[str] = None) -> dict:
        try:
            if os.path.exists(file_path):
                data = {"chat_id": chat_id}
                if caption:
                    data["caption"] = caption
                if reply_markup:
                    data["reply_markup"] = reply_markup
                if parse_mode:
                    data["parse_mode"] = parse_mode
                
                with open(file_path, "rb") as f:
                    response = httpx.post(self.api_url + method, data=data, files={file_param: f}, timeout=60.0)
                    return response.json().get("result", {})
            elif file_path.startswith(("http://", "https://")):
                json_data = {"chat_id": chat_id, file_param: file_path}
                if caption:
                    json_data["caption"] = caption
                if reply_markup:
                    json_data["reply_markup"] = reply_markup
                if parse_mode:
                    json_data["parse_mode"] = parse_mode
                
                response = httpx.post(self.api_url + method, json=json_data, timeout=30.0)
                return response.json().get("result", {})
            else:
                raise FileNotFoundOrInvalidURLError(
                    f"File not found or invalid URL: {file_path}"
                )
        except Exception as e:
            self.logger.error(f"Error in {method}: {e}", exc_info=True)
            return {}

    def send_photo(self, chat_id: int, photo: str, caption: Optional[str] = None, reply_markup: Optional[dict] = None, parse_mode: Optional[str] = None) -> dict:
        return self._send_file("sendPhoto", chat_id, photo, "photo", caption, reply_markup, parse_mode)

    def send_video(self, chat_id: int, video: str, caption: Optional[str] = None, reply_markup: Optional[dict] = None,parse_mode: Optional[str] = None) -> dict:
        """Send a video"""
        return self._send_file("sendVideo", chat_id, video, "video", caption, reply_markup, parse_mode)

    def send_audio(self, chat_id: int, audio: str, caption: Optional[str] = None, reply_markup: Optional[dict] = None, parse_mode: Optional[str] = None) -> dict:
        """Send an audio file"""
        return self._send_file("sendAudio", chat_id, audio, "audio", caption, reply_markup, parse_mode)

    def send_voice(self, chat_id: int, voice: str, caption: Optional[str] = None, reply_markup: Optional[dict] = None, parse_mode: Optional[str] = None ) -> dict:
        """Send a voice message"""
        if not os.path.exists(voice):
            raise FileNotFoundError(f"File {voice} not found")
        return self._send_file("sendVoice", chat_id, voice, "voice", caption, reply_markup, parse_mode)

    def send_document(self, chat_id: int, document: str, caption: Optional[str] = None, parse_mode: Optional[str] = None, reply_markup: Optional[dict] = None) -> dict:
        """Send a document"""
        return self._send_file("sendDocument", chat_id, document, "document", caption, reply_markup, parse_mode)

    def send_sticker(self, chat_id: int, sticker: str, reply_markup: Optional[dict] = None) -> dict:
        """Send a sticker"""
        params = {"chat_id": chat_id, "sticker": sticker}
        if reply_markup:
            params["reply_markup"] = reply_markup
        
        try:
            response = httpx.post(self.api_url + "sendSticker", json=params, timeout=30.0)
            return response.json().get("result", {})
        except Exception as e:
            self.logger.error(f"Error sending sticker: {e}")
            return {}

    def edit_message_text(self, chat_id: int, message_id: int, text: str, parse_mode: Optional[str] = None, reply_markup: Optional[dict] = None) -> dict:
        """Edit a message"""
        params = {"chat_id": chat_id, "message_id": message_id, "text": text}
        
        if parse_mode:
            params["parse_mode"] = parse_mode
        if reply_markup:
            params["reply_markup"] = reply_markup
        
        try:
            response = httpx.post(self.api_url + "editMessageText", json=params, timeout=30.0)
            return response.json().get("result", {})
        except Exception as e:
            self.logger.error(f"Error editing message: {e}")
            return {}

    def formatter(self, text: str, message: dict) -> str:
        """Format text with message data"""
        try:
            user = message.get("from", message.get("chat", {}))
            return text.format(
                first_name=user.get("first_name", ""),
                last_name=user.get("last_name", ""),
                full_name=f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                message_text=message.get("text", ""),
                user_id=user.get("id", ""),
                message_id=message.get("message_id", "")
            )
        except (KeyError, AttributeError):
            return text

    def get_me(self) -> dict:
        """Get bot information"""
        try:
            response = httpx.get(self.api_url + "getMe", timeout=10.0)
            return response.json()
        except Exception as e:
            self.logger.error(f"Error getting bot info: {e}")
            return {}

    def _send_handler_response(self, chat_id: int, handler: dict, message: dict):
        """Send response based on handler type"""
        response = handler["text"]
        
        if isinstance(response, str):
            self.send_message(chat_id, self.formatter(response, message), reply_markup=handler['reply_markup'], parse_mode=handler['parse_mode'])

        if callable(response):
            result = response(Message(**message)) if "text" in message else response()
            if result:
                return
        
        if isinstance(response, Photo):
            self.send_photo(
                chat_id, 
                self.formatter(response.url, message),
                caption=self.formatter(response.caption, message),
                reply_markup=handler["reply_markup"],
                parse_mode=handler["parse_mode"]
            )
        elif isinstance(response, Video):
            self.send_video(
                chat_id,
                self.formatter(response.url, message),
                caption=self.formatter(response.caption, message),
                reply_markup=handler["reply_markup"],
                parse_mode=handler["parse_mode"]
            )
        elif isinstance(response, Audio):
            self.send_audio(
                chat_id,
                self.formatter(response.url, message),
                caption=self.formatter(response.caption, message),
                reply_markup=handler["reply_markup"],
                parse_mode=handler["parse_mode"]
            )
        elif isinstance(response, Voice):
            self.send_voice(
                chat_id,
                self.formatter(response.url, message),
                caption=self.formatter(response.caption, message),
                reply_markup=handler["reply_markup"],
                parse_mode=handler["parse_mode"]
            )
        elif isinstance(response, Sticker):
            self.send_sticker(chat_id, response.file_id, reply_markup=handler["reply_markup"])
        elif isinstance(response, Document):
            self.send_document(
                chat_id,
                response.file_id,
                caption=self.formatter(response.caption, message),
                reply_markup=handler["reply_markup"],
                parse_mode=handler["parse_mode"]
            )
        elif isinstance(response, str):
            self.send_message(
                chat_id,
                self.formatter(response, message),
                parse_mode=handler["parse_mode"],
                reply_markup=handler["reply_markup"]
            )

    def process_callback(self, callback: dict):
        """Process callback queries"""
        message = callback.get("message", {})
        data = callback.get("data")
        chat_id = message.get("chat", {}).get("id")
        
        if not chat_id or not data:
            return
        
        handler = self.callback_handlers.get(data)
        if handler:
            self._send_handler_response(chat_id, handler, message)

    def process_messages(self, message: dict):
        """Process incoming messages"""
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")
        
        if not chat_id:
            return
        
        # Save user to database
        if self.auto_db and "from" in message:
            self.db.add_data("users", username=message["from"].get("username", ""), user_id=message["from"].get("id"))
        
        if self.admin_id and message.get("from", {}).get("id") == self.admin_id:
            self.when("/admin", "Welcome Admin!", reply_markup=KeyboardButton(["statistika📊"]))
            self.when("statistika📊", f"Foydalanuvchilar soni: {len(self.db.get_data('users'))}")
        
        # Get handler
        handler = self.handlers.get(text) or self.handlers.get("*")
        
        if handler:
            self._send_handler_response(chat_id, handler, message)

    def run(self):
        """Start the bot"""
        bot_info = self.get_me()
        
        if not bot_info.get("result"):
            raise Exception("No telegram bot found with the provided token")
        
        bot_data = bot_info["result"]
        self.logger.info(f"[@{bot_data['username']} - id={bot_data['id']}] successfully started")
        offset = 0
        while True:
            try:
                updates = self.get_updates(offset)
                
                for update in updates.get("result", []):
                    offset = update["update_id"] + 1
                    
                    if "callback_query" in update:
                        self.process_callback(update["callback_query"])
                    elif "message" in update:
                        self.process_messages(update["message"])
                        
            except KeyboardInterrupt:
                self.logger.info("Bot stopped by user")
                break
            except Exception as e:
                self.logger.error("Error occurred", exc_info=True)
