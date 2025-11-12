import logging
from pydantic import BaseModel, Field


class FileNotFoundOrInvalidURLError(Exception):
    """Raised when a file does not exist or the provided URL is invalid."""
    pass

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

class Document:
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

class User(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    surename: str | None = None 
    language_code: str
    last_name: str | None = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

class Chat(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    type: str

class Message(BaseModel):
    message_id: int
    from_user: User = Field(..., alias="from")
    chat: Chat
    date: int
    text: str
    entities: list
