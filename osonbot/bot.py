import os
import time
import httpx
from typing import Union
from .database import Database
from .utils import (
    FileNotFoundOrInvalidURLError, OsonBotError, UnsupportedHTTPMethodError, TelegramRequestError,
    TelegramAPIError, BotStartupError, UpdateProcessingError, MessageHandlerError,
    CallbackHandlerError, FormatterError, InvalidUpdateError, HandlerReturnTypeError,
    StateGroupNotFoundError,
    Photo, Video, Audio, Voice, Document, Sticker,
    setup_logger, 
    InlineKeyboardButton, RemoveKeyboardButton, URLKeyboardButton, KeyboardButton,
    Message, State
)

class Bot:
    def __init__(self, token, auto_db: bool = True, db_name: str = "database.db", admin_id: int = None):
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.client = httpx.Client(timeout=httpx.Timeout(30.0, connect=10.0), transport=httpx.HTTPTransport(retries=3))
        self.handlers = {}
        self.state_handlers = {}
        self.callback_handlers = {}
        self.admin_handlers = {}
        self.error_handlers = {}
        self.logger = setup_logger("osonbot")
        self.auto_db = auto_db
        if admin_id is not None:
            try:
                self.admin_id = int(admin_id)
            except (TypeError, ValueError) as error:
                raise ValueError("admin_id must be a numeric Telegram user ID.") from error
        else:
            self.admin_id = None
        if auto_db:
            self.db = Database(db_name)
            self.db.create_table("users", username=str, user_id=int)
        self.state = State()
        if self.admin_id is not None:
            self.admin_handlers["/admin"] = {
                "text": "Welcome Admin!",
                "parse_mode": None,
                "reply_markup": KeyboardButton(["statistika📊"]),
                "state": None,
            }
            self.admin_handlers["statistika📊"] = {
                "text": self._admin_statistics,
                "parse_mode": None,
                "reply_markup": None,
                "state": None,
            }

    def _admin_statistics(self, _message: Message):
        if not self.auto_db:
            return "Automatic database is disabled."
        return f"Foydalanuvchilar soni: {len(self.db.get_data('users'))}"

    def _handle_error(self, error: Exception, context: dict = None):
        context = context or {}
        setattr(error, "_osonbot_handled", True)
        handlers = sorted(
            self.error_handlers.items(),
            key=lambda item: len(item[0].mro()),
            reverse=True,
        )
        for error_type, handler in handlers:
            if isinstance(error, error_type):
                try:
                    return handler(error, context)
                except TypeError:
                    try:
                        return handler(error)
                    except Exception:
                        self.logger.error("Error handler failed: ", exc_info=True)
                        return None
                except Exception:
                    self.logger.error("Error handler failed: ", exc_info=True)
                    return None

        self.logger.error("Error occured: ", exc_info=(type(error), error, error.__traceback__))

    def error(self, exception: type[Exception] = Exception, handler=None):
        """Register an error handler as a decorator or a direct call.

        Decorator form::

            @bot.error(TelegramAPIError)
            def handle_api_error(error, context):
                ...

        Direct form::

            bot.error(TelegramAPIError, handle_api_error)

        Direct registration returns the bot so it can be chained like the
        message registration methods.
        """
        if not isinstance(exception, type) or not issubclass(exception, Exception):
            raise TypeError("exception must be an Exception subclass.")

        if handler is None:
            def decorator(func):
                if not callable(func):
                    raise TypeError("Error handler must be callable.")
                self.error_handlers[exception] = func
                return func
            return decorator

        if not callable(handler):
            raise TypeError("Error handler must be callable.")
        self.error_handlers[exception] = handler
        return self

    def _telegram_json(self, response, request: str):
        try:
            data = response.json()
        except ValueError as e:
            error = TelegramAPIError(request, "Telegram returned invalid JSON.", response.status_code)
            self._handle_error(error, {"request": request})
            raise error from e

        if not data.get("ok", False):
            error = TelegramAPIError(
                request,
                data.get("description"),
                data.get("error_code", response.status_code),
                data
            )
            self._handle_error(error, {"request": request, "response": data})
            raise error
        return data

    def _telegram_result(self, response, request: str):
        return self._telegram_json(response, request)["result"]

    def _request_error(self, error: httpx.RequestError, request: str, context: dict = None):
        handled_error = TelegramRequestError(str(error))
        error_context = {"request": request}
        if context:
            error_context.update(context)
        self._handle_error(handled_error, error_context)
        return handled_error

    def _message_user_id(self, message: dict):
        user = message.get("from") or message.get("chat")
        if not user or "id" not in user:
            raise InvalidUpdateError("Message update does not contain a user or chat id.")
        return user["id"]

    def _send_handler_response(self, chat_id, response, handled: dict, message: dict):
        if response is None:
            return
        if isinstance(response, Photo):
            return self.send_photo(chat_id, response.url, caption=self.formatter(response.caption, message), reply_markup=handled['reply_markup'], parse_mode=handled['parse_mode'])
        if isinstance(response, Video):
            return self.send_video(chat_id, response.url, caption=self.formatter(response.caption, message), reply_markup=handled['reply_markup'], parse_mode=handled['parse_mode'])
        if isinstance(response, Audio):
            return self.send_audio(chat_id, response.url, caption=self.formatter(response.caption, message), reply_markup=handled['reply_markup'], parse_mode=handled['parse_mode'])
        if isinstance(response, Voice):
            return self.send_voice(chat_id, response.url, caption=self.formatter(response.caption, message), reply_markup=handled['reply_markup'], parse_mode=handled['parse_mode'])
        if isinstance(response, Sticker):
            return self.send_sticker(chat_id, response.file_id, reply_markup=handled['reply_markup'])
        if isinstance(response, str):
            return self.send_message(chat_id, self.formatter(response, message), parse_mode=handled['parse_mode'], reply_markup=handled['reply_markup'])
        if isinstance(response, Document):
            return self.send_document(chat_id, response.file_id, caption=self.formatter(response.caption, message), reply_markup=handled['reply_markup'], parse_mode=handled['parse_mode'])
        raise HandlerReturnTypeError(f"Unsupported handler return type: {type(response).__name__}")

    def send_request(self, method: str, request: str, params: dict = None, data: dict = None, json: dict = None):
        try:
            if method == "post":
                return self.client.post(self.api_url + request, params=params, data=data, json=json)
            elif method == "get":
                return self.client.get(self.api_url + request, params=params)
            raise UnsupportedHTTPMethodError(f"Unsupported HTTP method: {method}")
        except httpx.RequestError as e:
            raise self._request_error(e, request, {"method": method}) from e
        except Exception as e:
            self._handle_error(e, {"request": request, "method": method})
            raise

    def when(self, condition: str | list[str], text=None, parse_mode: str = None, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None, state: str = None):
        """Register a message handler directly or with decorator syntax."""
        if state is not None:
            self.state.resolve(state)

        if text is None:
            def decorator(func):
                if not callable(func):
                    raise TypeError("Message handler must be callable.")
                return self.when(condition, func, parse_mode, reply_markup, state)
            return decorator

        if condition:
            handler = {"text": text, 'parse_mode': parse_mode, 'reply_markup': reply_markup, "state": state}
            if isinstance(condition, list):
                for cond in condition:
                    if isinstance(cond, str) and cond.startswith("state:"):
                        self.state.resolve(cond)
                    self.handlers[cond] = handler
            else:
                if isinstance(condition, str) and condition.startswith("state:"):
                    self.state.resolve(condition)
                self.handlers[condition] = handler
        return self

    def c_when(self, condition: str | list[str], text=None, parse_mode: str = None, reply_markup: str = None):
        """Register a callback handler directly or with decorator syntax."""
        if text is None:
            def decorator(func):
                if not callable(func):
                    raise TypeError("Callback handler must be callable.")
                return self.c_when(condition, func, parse_mode, reply_markup)
            return decorator

        if condition:
            if isinstance(condition, list):
                for cond in condition:
                    self.callback_handlers[cond] = {"text": text, 'parse_mode': parse_mode, 'reply_markup': reply_markup}
            else:
                self.callback_handlers[condition] = {'text': text, "parse_mode": parse_mode, "reply_markup": reply_markup}
        return self

    def when_state(self, state: str, text=None, parse_mode: str = None, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None, next_state: str = None):
        """Register a response or callable for a state without using ``when``."""
        if not isinstance(state, str) or not state:
            raise ValueError("state must be a non-empty string.")
        if text is None:
            def decorator(func):
                if not callable(func):
                    raise TypeError("State handler must be callable.")
                return self.when_state(state, func, parse_mode, reply_markup, next_state)
            return decorator

        if ":" in state:
            group, state_name = state.split(":", 1)
            state_key = self.state.key(group, state_name)
        else:
            group = state
            if group not in self.state.order:
                raise StateGroupNotFoundError(f"State group not found: {group}")
            state_key = self.state.key(group, self.state.order[group][-1])

        if next_state is None and ":" in state:
            next_state = self.state.next(state)
        if next_state is not None:
            self.state.resolve(next_state)

        self.state_handlers[state_key] = {
            "text": text,
            "parse_mode": parse_mode,
            "reply_markup": reply_markup,
            "state": next_state,
        }
        return self

    def get_updates(self, offset: int):
        try:
            response = self.client.get(self.api_url+"getUpdates", params={'offset': offset})
            return self._telegram_json(response, "getUpdates")
        except httpx.RequestError as e:
            raise self._request_error(e, "getUpdates") from e
    
    def send_message(self, chat_id, text: str, parse_mode: str = None, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None):
        params = {'chat_id': chat_id, "text": text}
        if parse_mode:
            params['parse_mode'] = parse_mode
        if reply_markup:
            params['reply_markup'] = reply_markup
        try:
            response = self.client.post(self.api_url+"sendMessage", json=params)
            return self._telegram_result(response, "sendMessage")
        except httpx.RequestError as e:
            raise self._request_error(e, "sendMessage", {"chat_id": chat_id}) from e
    
    def send_photo(self, chat_id, photo: str, caption: str = None, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None, parse_mode: str = None):
        try:
            if os.path.exists(photo):
                data = {"chat_id": chat_id, 'caption': caption}
                if reply_markup:
                    data['reply_markup'] = reply_markup
                if parse_mode:
                    data['parse_mode'] = parse_mode
                with open(photo, 'rb') as p:
                    response = self.client.post(self.api_url+"sendPhoto", data=data, files={"photo": p})
                    return self._telegram_result(response, "sendPhoto")
            elif "https://" in photo or "http://" in photo:
                json = {"chat_id": chat_id, "photo": photo, 'caption': caption}
                if reply_markup:
                    json['reply_markup'] = reply_markup
                if parse_mode:
                    json['parse_mode'] = parse_mode
                response = self.client.post(self.api_url+"sendPhoto", json=json)
                return self._telegram_result(response, "sendPhoto")
            else:
                raise FileNotFoundOrInvalidURLError(f"Photo not found or invalid URL: {photo}")
        except httpx.RequestError as e:
            raise self._request_error(e, "sendPhoto", {"chat_id": chat_id}) from e
        except Exception as e:
            if isinstance(e, OsonBotError) and getattr(e, "_osonbot_handled", False):
                raise
            self._handle_error(e, {"request": "sendPhoto", "chat_id": chat_id})
            raise

    def send_video(self, chat_id, video: str, caption, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None, parse_mode: str = None):
        try:
            if os.path.exists(video):
                data = {"chat_id": chat_id, 'caption': caption}
                if reply_markup:
                    data['reply_markup'] = reply_markup
                if parse_mode:
                    data['parse_mode'] = parse_mode
                with open(video, 'rb') as v:
                    response = self.client.post(self.api_url+"sendVideo", data=data, files={"video": v})
                    return self._telegram_result(response, "sendVideo")
            elif "https://" in video or "http://" in video:
                json = {"chat_id": chat_id, "video": video, 'caption': caption}
                if reply_markup:
                    json['reply_markup'] = reply_markup
                if parse_mode:
                    json['parse_mode'] = parse_mode
                response = self.client.post(self.api_url+"sendVideo", json=json)
                return self._telegram_result(response, "sendVideo")
            else:
                raise FileNotFoundOrInvalidURLError(f"Video not found or invalid URL: {video}")
        except httpx.RequestError as e:
            raise self._request_error(e, "sendVideo", {"chat_id": chat_id}) from e
        except Exception as e:
            if isinstance(e, OsonBotError) and getattr(e, "_osonbot_handled", False):
                raise
            self._handle_error(e, {"request": "sendVideo", "chat_id": chat_id})
            raise

    def send_audio(self, chat_id, audio: str, caption, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None, parse_mode: str = None):
        try:
            if os.path.exists(audio):
                data = {"chat_id": chat_id, 'caption': caption}
                if reply_markup:
                    data['reply_markup'] = reply_markup
                if parse_mode:
                    data['parse_mode'] = parse_mode
                with open(audio, 'rb') as a:
                    response = self.client.post(self.api_url+"sendAudio", data=data, files={"audio": a})
                    return self._telegram_result(response, "sendAudio")
            elif "https://" in audio or "http://" in audio:
                json = {"chat_id": chat_id, "audio": audio, 'caption': caption, 'reply_markup': reply_markup}
                if reply_markup:
                    json['reply_markup'] = reply_markup
                if parse_mode:
                    json['parse_mode'] = parse_mode
                response = self.client.post(self.api_url+"sendAudio", json=json)
                return self._telegram_result(response, "sendAudio")
            else:
                raise FileNotFoundOrInvalidURLError(f"Audio not found or invalid URL: {audio}")
        except httpx.RequestError as e:
            raise self._request_error(e, "sendAudio", {"chat_id": chat_id}) from e
        except Exception as e:
            if isinstance(e, OsonBotError) and getattr(e, "_osonbot_handled", False):
                raise
            self._handle_error(e, {"request": "sendAudio", "chat_id": chat_id})
            raise
    
    def send_voice(self, chat_id, voice: str, caption, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None, parse_mode: str = None):
        try:
            if os.path.exists(voice):
                data = {"chat_id": chat_id, 'caption': caption}
                if reply_markup:
                    data['reply_markup'] = reply_markup
                if parse_mode:
                    data['parse_mode'] = parse_mode
                with open(voice, 'rb') as v:
                    response = self.client.post(self.api_url+"sendVoice", data=data, files={"voice": v})
                    return self._telegram_result(response, "sendVoice")
            else:
                raise FileNotFoundError(f"file {voice} not found. Make sure it exists")
        except httpx.RequestError as e:
            raise self._request_error(e, "sendVoice", {"chat_id": chat_id}) from e
        except Exception as e:
            if isinstance(e, OsonBotError) and getattr(e, "_osonbot_handled", False):
                raise
            self._handle_error(e, {"request": "sendVoice", "chat_id": chat_id})
            raise
    
    def send_sticker(self, chat_id, sticker: str, reply_markup: dict = None):
        params = {"chat_id": chat_id, "sticker": sticker}
        if reply_markup:
            params['reply_markup'] = reply_markup
        try:
            response = self.client.post(self.api_url + "sendSticker", json=params)
            return self._telegram_result(response, "sendSticker")
        except httpx.RequestError as e:
            raise self._request_error(e, "sendSticker", {"chat_id": chat_id}) from e
    
    def send_document(self, chat_id, document: str, caption: str = None, parse_mode: str = None, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None):
        try:
            if os.path.exists(document):
                data = {"chat_id": chat_id, 'caption': caption}
                if reply_markup:
                    data['reply_markup'] = reply_markup
                if parse_mode:
                    data['parse_mode'] = parse_mode
                with open(document, 'rb') as v:
                    response = self.client.post(self.api_url+"sendDocument", data=data, files={"document": v})
                    return self._telegram_result(response, "sendDocument")
            elif "https://" in document or "http://" in document:
                json = {"chat_id": chat_id, "document": document, 'caption': caption}
                if reply_markup:
                    json['reply_markup'] = reply_markup
                if parse_mode:
                    json['parse_mode'] = parse_mode
                response = self.client.post(self.api_url+"sendDocument", json=json)
                return self._telegram_result(response, "sendDocument")
            else:
                raise FileNotFoundOrInvalidURLError(f"document not found or invalid URL: {document}")
        except httpx.RequestError as e:
            raise self._request_error(e, "sendDocument", {"chat_id": chat_id}) from e
        except Exception as e:
            if isinstance(e, OsonBotError) and getattr(e, "_osonbot_handled", False):
                raise
            self._handle_error(e, {"request": "sendDocument", "chat_id": chat_id})
            raise

    def edit_message_text(self, chat_id: int, message_id: int, text: str, parse_mode: str = None, reply_markup: Union[KeyboardButton, InlineKeyboardButton, URLKeyboardButton, None] = None):
        params = {'chat_id': chat_id, 'message_id': message_id, 'text': text}
        if parse_mode:
            params['parse_mode'] = parse_mode
        if reply_markup:
            params['reply_markup'] = reply_markup
        try:
            response = self.client.post(self.api_url + "editMessageText", json=params)
            return self._telegram_result(response, "editMessageText")
        except httpx.RequestError as e:
            raise self._request_error(e, "editMessageText", {"chat_id": chat_id, "message_id": message_id}) from e
    
    def formatter(self, text: str, message):
        try:
            first_name = message['from'].get('first_name', "")
            last_name = message['from'].get('last_name', "")
            return text.format(
                    first_name=first_name,
                    last_name=last_name,
                    full_name=f"{first_name} {last_name}".strip(),
                    message_text=message['text'],
                    user_id=message['from']['id'],
                    message_id=message['message_id'],
                    msg=message
                )
        except Exception as e:
            try:
                return text.format(
                        first_name=message['chat']['first_name'] if 'first_name' in message['chat'] else "",
                        last_name=message['chat']['last_name'] if 'last_name' in message['chat'] else "",
                        full_name=f"{message['chat']['first_name'] if 'first_name' in message['chat'] else ''} {message['chat']['last_name'] if 'last_name' in message['chat'] else ''}",
                        message_text=message['text'],
                        user_id=message['from']['id'],
                        message_id=message['message_id'],
                        msg=message
                    )
            except Exception as e:
                error = FormatterError(str(e))
                self._handle_error(error, {"text": text, "message": message})
                return text
    
    def get_me(self):
        try:
            response = self.client.get(self.api_url + "getMe")
            return self._telegram_json(response, "getMe")
        except httpx.RequestError as e:
            raise self._request_error(e, "getMe") from e

    def _process_callback(self, callback):
        message = callback.get("message", {})
        data = callback.get('data')
        chat_id = message.get("chat", {}).get("id")
        if chat_id is None:
            raise InvalidUpdateError("Callback update does not contain a chat id.")
        handled = self.callback_handlers.get(data)
        
        if not handled:
            return

        response = handled['text']
        if callable(response):
            response = response(callback)
        self._send_handler_response(chat_id, response, handled, message)

    def process_callback(self, callback):
        try:
            return self._process_callback(callback)
        except Exception as e:
            if isinstance(e, OsonBotError):
                if not getattr(e, "_osonbot_handled", False):
                    self._handle_error(e, {"callback": callback})
                raise
            error = e if isinstance(e, CallbackHandlerError) else CallbackHandlerError(str(e))
            self._handle_error(error, {"callback": callback})
            raise error from e
    
    def _apply_state_transition(self, user_id: int, handled: dict):
        next_state = handled.get("state")
        if next_state is None:
            self.state.clear(user_id)
        else:
            self.state.set(user_id, next_state)
    
    def _process_messages(self, message):
        user_id = self._message_user_id(message)
        self.state.active_user_id = user_id
        chat_id = message.get("chat", {}).get("id", user_id)

        if self.auto_db:
            user = message.get("from", {})
            self.db.add_data("users", username=user.get("username"), user_id=user_id)

        if "text" in message:
            text = message.get("text", "")
            chat_id = message.get("chat", {}).get("id", user_id)
            state_response_transition = False

            if user_id == self.admin_id and text in self.admin_handlers:
                handled = self.admin_handlers[text]
            else:
                current_state = self.state.get(user_id)
                state_key = self.state.key(current_state["group"], current_state["state"]) if current_state else None
                if state_key and state_key in self.state_handlers:
                    self.state.save(user_id, text)
                    handled = self.state_handlers[state_key]
                    next_state = handled.get("state")
                    if next_state is not None:
                        self.state.set(user_id, next_state)
                        next_key = self.state.key(next_state)
                        handled = self.state_handlers.get(next_key, handled)
                        state_response_transition = True
                elif state_key and state_key in self.handlers:
                    self.state.save(user_id, text)
                    handled = self.handlers.get(state_key)
                else:
                    handled = self.handlers.get(text) or self.handlers.get("*")
            
            if not handled:
                return
            
            if callable(handled['text']):
                returned = handled['text'](Message(**message))
                self._send_handler_response(chat_id, returned, handled, message)
            
            elif handled['text'] is not None:
                self._send_handler_response(chat_id, handled['text'], handled, message)

            if not state_response_transition:
                self._apply_state_transition(user_id, handled)
            elif handled.get("state") is None:
                self.state.clear(user_id)
        
        elif "photo" in message:
            hv = self.handlers.get(Photo)
            if not hv:
                return
            self.send_message(chat_id, hv['text'], parse_mode=hv['parse_mode'], reply_markup=hv['reply_markup'])
        elif "video" in message:
            hv = self.handlers.get(Video)
            if not hv:
                return
            self.send_message(chat_id, hv['text'], parse_mode=hv['parse_mode'], reply_markup=hv['reply_markup'])
        elif "sticker" in message:
            hv = self.handlers.get(Sticker)
            if not hv:
                return
            self.send_message(chat_id, hv['text'], parse_mode=hv['parse_mode'], reply_markup=hv['reply_markup'])
        elif "document" in message:
            hv = self.handlers.get(Document)
            if not hv:
                return
            self.send_message(chat_id, hv['text'], parse_mode=hv['parse_mode'], reply_markup=hv['reply_markup'])

    def process_messages(self, message):
        try:
            return self._process_messages(message)
        except Exception as e:
            if isinstance(e, OsonBotError):
                if not getattr(e, "_osonbot_handled", False):
                    self._handle_error(e, {"message": message})
                raise
            error = e if isinstance(e, MessageHandlerError) else MessageHandlerError(str(e))
            self._handle_error(error, {"message": message})
            raise error from e
    
    def run(self):
        getme = self.get_me()
        try:
            self.logger.info(f"[@{getme['result']['username']} - id={getme['result']['id']}] successfully started")
        except Exception as e:
            error = BotStartupError("No telegram bot found based on the token")
            self._handle_error(error, {"response": getme})
            raise error from e
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
                if isinstance(e, OsonBotError):
                    if not getattr(e, "_osonbot_handled", False):
                        self._handle_error(e, {"offset": offset})
                    time.sleep(1)
                    continue
                error = e if isinstance(e, UpdateProcessingError) else UpdateProcessingError(str(e))
                self._handle_error(error, {"offset": offset})
                time.sleep(1)
