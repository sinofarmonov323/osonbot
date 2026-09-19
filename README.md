# osonbot

A lightweight, easy-to-use Python framework for building Telegram bots with handlers, media support, keyboard tooling, and state-based flows.

[![PyPI version](https://img.shields.io/pypi/v/osonbot.svg)](https://pypi.org/project/osonbot/)
[![Python versions](https://img.shields.io/pypi/pyversions/osonbot.svg)](https://pypi.org/project/osonbot/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/sinofarmonov323/osonbot/blob/main/LICENSE)

> Official maintainer: Sino Farmonov

## Why osonbot?

- Simple `Bot` API for Telegram bot handlers
- Built-in state management for multi-step logic
- Media helpers for photos, videos, audio, stickers, and documents
- Keyboard and inline keyboard utilities
- Fast prototyping and clean, readable code

## Installation

```bash
pip install osonbot
```

## Quick start

```python
from osonbot import Bot

bot = Bot("YOUR_BOT_TOKEN")

bot.when("/start", "Hello {first_name}! Welcome to my bot.")
bot.when("{message_text}", "You said: {message_text}")

bot.run()
```

## Handling messages

```python
bot.when("MESSAGE_YOU_WANT_TO_HANDLE", "TEXT_YOU_WANT_TO_SEND_WHEN_MESSAGE_IS_HANDLED")
```

### Example

```python
from osonbot import Bot

bot = Bot("YOUR_BOT_TOKEN")

bot.when("/start", "Hello {first_name}!")
```

### Using a function

```python
from osonbot import Bot

bot = Bot("YOUR_BOT_TOKEN")


def greet(msg):
    # task 1
    # task 2
    return "All the tasks are done"


bot.when("/do_task", greet)
```

If you run this code above, you will get `All the tasks are done` back from your Telegram bot.

### Template fields

The library automatically formats these values for you:

- `{first_name}`: Telegram user's first name
- `{last_name}`: Telegram user's last name
- `{full_name}`: Telegram user's full name
- `{message_text}`: message text sent by the user
- `{user_id}`: Telegram user's ID
- `{message_id}`: message ID

#### Examples

```python
bot.when("/firstname", "your first name is {first_name}")
bot.when("/fullname", "your full name is {full_name}")
bot.when("/lastname", "your last name is {last_name}")
bot.when("/text", "you sent {message_text}")
bot.when("/id", "your telegram id is {user_id}")
bot.when("/msgid", "your message's id is {message_id}")
```

## State management

Use registered states to create multi-step conversations.

```python
from osonbot import Bot

bot = Bot("YOUR_BOT_TOKEN")
bot.state.register("survey", states=["welcome", "name", "done"])

bot.when("/start", "Tell me your name.", state="survey:welcome")

bot.when_state(
    state="survey:welcome",
    text="Tell me your name.",
    next_state="survey:name",
)

bot.when_state(
    state="survey:name",
    text="Thanks! Your answer was saved.",
)

bot.run()
```

## Sending media

To handle media, use `when` with the appropriate media object instead of passing a plain string.

```python
from osonbot import Bot, Photo, Video, Audio, Voice, Sticker, Document

bot = Bot("YOUR_BOT_TOKEN")

bot.when(Photo, "you sent a photo")
bot.when(Video, "you sent a video")
bot.when(Audio, "you sent an audio")
bot.when(Voice, "you sent a voice")
bot.when(Sticker, "you sent a sticker")
bot.when(Document, "document is received")
```

### Example: sending media

```python
from osonbot import Bot, Photo, Video, Audio, Voice, Sticker, Document

bot = Bot("YOUR_BOT_TOKEN")

bot.when("/photo", Photo("URL_OR_PATH_TO_PHOTO", caption="optional"))
bot.when("/video", Video("URL_OR_PATH_TO_VIDEO", caption="optional"))
# same with Audio, Voice, Sticker, and Document
```

## Editing messages

You can edit message text using the built-in message editing utilities.

```python
bot.edit_message_text(chat_id, message_id, "new message")
```

This supports parse mode, caption, and reply markup depending on your use case.

## Sending buttons

### Keyboard buttons

```python
from osonbot import Bot, KeyboardButton

bot = Bot("YOUR_BOT_TOKEN")

row1 = ["Button 1", "Button 2"]
row2 = ["Button 3"]
row3 = ["Button 4", "Button 5"]

bot.when("hi", "hi, {first_name}\nchoose", reply_markup=KeyboardButton(row1, row2, row3))
```

You can give as many buttons as you want. `KeyboardButton` supports `resize_keyboard` (default `True`) and `one_time_keyboard` (default `False`).

### Inline keyboard buttons

```python
from osonbot import Bot, InlineKeyboardButton

bot = Bot("YOUR_BOT_TOKEN")

InlineKeyboardButton(
    [["BUTTON_TEXT", "BUTTON_CALLBACK_DATA"], ["BUTTON_TEXT", "BUTTON_CALLBACK_DATA"]],
    [same here]
)
```

## Error handling

You can register error handlers to intercept exceptions.

```python
from osonbot import Bot

bot = Bot("YOUR_BOT_TOKEN")

@bot.error(Exception)
def handle_error(error):
    print("Something went wrong:", error)
```

## Example bot script

```python
from osonbot import Bot, Message

bot = Bot("8380176186:AAHun7E7_IPgIv2tpVeeriYKt8dEH3QUPv0")

bot.state.register("State_Name", states=["state1", "state2", "state3"])


def send_states(message: Message):
    state_values = bot.state.data(message.from_user.id, "State_Name")
    return f"Current state values:\n{state_values}"


bot.when("/states", send_states)

bot.when("/start", "You are in state 1\nEnter something to go to state 2", state="State_Name:state1")

bot.when_state(
    state="State_Name:state1",
    text="You are in state 1\nEnter something to go to state 2",
    next_state="State_Name:state2",
)

bot.when_state(
    state="State_Name:state2",
    text="You're in a state 2 now\nIt looks like the code is working fine\nSend me your username to go to the last state",
)


def handle_state(message: Message):
    bot.state.save("State_Name", state3="@" + (message.from_user.username or "unknown"))
    return "State test completed."


bot.when_state("State_Name", handle_state)


if __name__ == "__main__":
    bot.run()
```

## Project links

- GitHub: https://github.com/sinofarmonov323/osonbot
- PyPI: https://pypi.org/project/osonbot/
- Issues: https://github.com/sinofarmonov323/osonbot/issues

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
