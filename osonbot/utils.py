import logging
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class OsonBotError(Exception):
    """Base exception for osonbot errors."""
    pass

class FileNotFoundOrInvalidURLError(OsonBotError):
    """Raised when a file does not exist or the provided URL is invalid."""
    pass

class BotConfigurationError(OsonBotError):
    """Raised when the bot is configured incorrectly."""
    pass

class UnsupportedHTTPMethodError(OsonBotError):
    """Raised when an unsupported HTTP method is used."""
    pass

class TelegramRequestError(OsonBotError):
    """Raised when Telegram cannot be reached."""
    pass

class TelegramAPIError(OsonBotError):
    """Raised when Telegram returns an unsuccessful API response."""

    def __init__(self, method: str, description: str = None, status_code: int = None, response: dict = None):
        self.method = method
        self.description = description or "Telegram API request failed."
        self.status_code = status_code
        self.response = response or {}
        super().__init__(self.description)

class BotStartupError(OsonBotError):
    """Raised when the bot cannot start."""
    pass

class UpdateProcessingError(OsonBotError):
    """Raised when an update cannot be processed."""
    pass

class MessageHandlerError(UpdateProcessingError):
    """Raised when a message handler fails."""
    pass

class CallbackHandlerError(UpdateProcessingError):
    """Raised when a callback handler fails."""
    pass

class FormatterError(OsonBotError):
    """Raised when message formatting fails."""
    pass

class InvalidUpdateError(UpdateProcessingError):
    """Raised when an incoming Telegram update has an invalid shape."""
    pass

class HandlerReturnTypeError(UpdateProcessingError):
    """Raised when a handler returns an unsupported value."""
    pass

class StateError(OsonBotError):
    """Base exception for state-related errors."""
    pass

class StateAlreadyExistsError(StateError):
    """Raised when a state group already exists."""
    pass

class StateDefinitionError(StateError):
    """Raised when a state group definition is invalid."""
    pass

class StateGroupNotFoundError(StateError):
    """Raised when a state group does not exist."""
    pass

class StateNotFoundError(StateError):
    """Raised when a state name does not exist in any state group."""
    pass

class StateAmbiguousError(StateError):
    """Raised when a bare state name exists in multiple groups."""
    pass

def KeyboardButton(
    *rows: List[str],
    resize_keyboard: bool = True,
    one_time_keyborad: bool = False,
    one_time_keyboard: Optional[bool] = None,
):
    if one_time_keyboard is not None:
        one_time_keyborad = one_time_keyboard
    return {
        "keyboard": list(rows),
        'resize_keyboard': resize_keyboard,
        'one_time_keyboard': one_time_keyborad
    }

def InlineKeyboardButton(*rows: List[List[Tuple[str, str]]]) -> Dict[str, list]:
    keyboard = []
    for row in rows:
        keyboard_row = [{"text": text, "callback_data": data} for text, data in row]
        keyboard.append(keyboard_row)
    return {"inline_keyboard": keyboard}

def URLKeyboardButton(*rows: List[List[Tuple[str, str]]]) -> Dict[str, list]:
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

class Document:
    def __init__(self, file_id, caption=""):
        self.file_id = file_id
        self.caption = caption

class Sticker:
    def __init__(self, file_id):
        self.file_id = file_id

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not any(getattr(handler, "_osonbot_handler", False) for handler in logger.handlers):
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler._osonbot_handler = True
        logger.addHandler(stream_handler)

    return logger

class User(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    language_code: Optional[str] = None
    username: Optional[str] = None
    last_name: Optional[str] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

class Chat(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    type: str

class Message(BaseModel):
    message_id: int
    from_user: User = Field(..., alias="from")
    chat: Chat
    date: int
    text: Optional[str] = None
    entities: Optional[List[Any]] = None

    class Config:
        allow_population_by_field_name = True

class State:
    def __init__(self, group: Optional[str] = None, **states):
        self.handlers = {}
        self.order = {}
        self.user_state = {}
        self.user_data = {}
        self.active_user_id = None
        if group is not None and states:
            self.add(group, *states.keys())

    def add(self, group: str, *states: str):
        return self.register(group, list(states))

    def register(self, group: str, columns: Optional[List[str]] = None):
        if not group or not isinstance(group, str):
            raise StateDefinitionError("State group name must be a non-empty string.")
        if group in self.handlers:
            raise StateAlreadyExistsError(f"State group already exists: {group}")
        states = columns or []
        if not states:
            raise StateDefinitionError("You must provide at least one state.")
        if len(states) != len(set(states)):
            raise StateDefinitionError("State names inside a group must be unique.")
        for state in states:
            if not state or not isinstance(state, str):
                raise StateDefinitionError("State names must be non-empty strings.")

        self.handlers[group] = {state: None for state in states}
        self.order[group] = list(states)
        return self
    
    def add_state(self, group: str, **states):
        if states:
            return self.add(group, *states.keys())
        raise StateDefinitionError("You must provide at least one state.")

    def exists(self, state: str) -> bool:
        try:
            self.resolve(state)
            return True
        except StateError:
            return False

    def get_group(self, state: str) -> str:
        return self.resolve(state)[0]

    def key(self, group: str, state: Optional[str] = None) -> str:
        if state is None:
            group, state = self.resolve(group)
        elif group not in self.handlers or state not in self.handlers[group]:
            raise StateNotFoundError(f"State not found: {group}:{state}")
        return f"state:{group}:{state}"

    def resolve(self, state: str) -> Tuple[str, str]:
        if not state or not isinstance(state, str):
            raise StateDefinitionError("State reference must be a non-empty string.")

        parts = state.split(":")
        if len(parts) == 3 and parts[0] == "state":
            group, state_name = parts[1], parts[2]
        elif len(parts) == 2:
            group, state_name = parts[0], parts[1]
        elif len(parts) == 1:
            matches = [(group, states) for group, states in self.handlers.items() if state in states]
            if not matches:
                raise StateNotFoundError(f"State not found: {state}")
            if len(matches) > 1:
                groups = ", ".join(group for group, _ in matches)
                raise StateAmbiguousError(f"State '{state}' exists in multiple groups: {groups}")
            group, _ = matches[0]
            state_name = state
        else:
            raise StateDefinitionError("State reference must be 'state:group:name', 'group:name', or 'name'.")

        if group not in self.handlers:
            raise StateGroupNotFoundError(f"State group not found: {group}")
        if state_name not in self.handlers[group]:
            raise StateNotFoundError(f"State not found: {group}:{state_name}")
        return group, state_name

    def set(self, user_id: int, state: str):
        group, state_name = self.resolve(state)
        self.user_state[user_id] = {"group": group, "state": state_name}
        self.user_data.setdefault(user_id, {}).setdefault(group, self.handlers[group].copy())
        return self

    def save(self, user_id: int, value: Any = None, state: Optional[str] = None, **values):
        if isinstance(user_id, str) and values:
            group = user_id
            if group not in self.handlers:
                raise StateGroupNotFoundError(f"State group not found: {group}")
            active_user_id = self.active_user_id
            if active_user_id is None:
                raise StateNotFoundError("No active user is available for this state save.")
            current_data = self.user_data.setdefault(active_user_id, {}).setdefault(
                group, self.handlers[group].copy()
            )
            for state_name, state_value in values.items():
                if state_name not in self.handlers[group]:
                    raise StateNotFoundError(f"State not found: {group}:{state_name}")
                current_data[state_name] = state_value
            return self

        current = self.get(user_id)
        if not current and state is None:
            raise StateNotFoundError(f"No active state for user: {user_id}")

        if current:
            group = current["group"]
            state_name = current["state"]
        else:
            group, state_name = self.resolve(state)
        if state_name not in self.handlers[group]:
            raise StateNotFoundError(f"State not found: {state_name}")

        self.user_data.setdefault(user_id, {}).setdefault(group, self.handlers[group].copy())
        self.user_data[user_id][group][state_name] = value
        return self

    def next(self, state: str) -> Optional[str]:
        group, state_name = self.resolve(state)
        states = self.order[group]
        index = states.index(state_name) + 1
        if index >= len(states):
            return None
        return f"{group}:{states[index]}"

    def get(self, user_id: int):
        return self.user_state.get(user_id)

    def data(self, user_id: int, group: Optional[str] = None):
        if group is not None and group not in self.handlers:
            raise StateGroupNotFoundError(f"State group not found: {group}")
        data = self.user_data.get(user_id, {})
        return data.get(group, {}) if group else data

    def clear(self, user_id: int):
        self.user_state.pop(user_id, None)
        return self

    def reset(self, user_id: int, group: Optional[str] = None):
        if group is not None and group not in self.handlers:
            raise StateGroupNotFoundError(f"State group not found: {group}")
        if group is None:
            self.user_data.pop(user_id, None)
            self.clear(user_id)
        else:
            self.user_data.get(user_id, {}).pop(group, None)
            current = self.get(user_id)
            if current and current["group"] == group:
                self.clear(user_id)
        return self

    def __contains__(self, group: str):
        return group in self.handlers

    def __getitem__(self, group: str):
        if group not in self.handlers:
            raise StateGroupNotFoundError(f"State group not found: {group}")
        return self.handlers[group]
