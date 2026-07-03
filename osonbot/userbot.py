from telethon.sync import TelegramClient, events

class UserBot(TelegramClient):
    def __init__(self, session_name, api_id, api_hash, **kwargs):
        super().__init__(session_name, api_id, api_hash, **kwargs)
        self.handlers = {}

    def answer(self, condition: str, response: str):
        self.handlers[condition] = response
        return self

    def run(self):
        print(events.raw)
        self.start()
        self.run_until_disconnected()
