import json
import threading
from osonbot import Bot


class BotBuilder:
    def __init__(self, storage_file="bots.json"):
        """Initialize the bot builder and load all existing bots."""
        self.storage_file = storage_file
        self.bots = []
        self._load()

    def _load(self):
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                self.bots = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.bots = []

    def _save(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(self.bots, f, indent=2, ensure_ascii=False)

    def add_bot(self, token: str, owner_id: int):
        """Add a new bot owned by a user."""
        for bot in self.bots:
            if bot["token"] == token:
                return False

        new_bot = {
            "token": token,
            "owner_id": owner_id,
            "commands": []
        }

        self.bots.append(new_bot)
        self._save()

        threading.Thread(target=self._run_bot, args=(token,), daemon=True).start()
        return True

    def when(self, token: str, command: str, response: str):
        """Add a text command to a bot."""
        for bot in self.bots:
            if bot["token"] == token:
                bot["commands"].append({"command": command, "response": response})
                self._save()
                return True
        return False

    def get_user_bot(self, owner_id: int):
        """Get the bot that belongs to a specific user."""
        for bot in self.bots:
            if bot["owner_id"] == owner_id:
                return bot
        return None

    def _run_bot(self, token: str):
        """Run a bot and handle its messages."""
        bot = Bot(token)

        def handler(msg):
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")
            
            for b in self.bots:
                if b["token"] == token:
                    for cmd in b["commands"]:
                        if text == cmd["command"]:
                            bot.send_message(chat_id, cmd["response"])
                            return

            bot.send_message(chat_id, "❓ Unknown command.")

        bot.when("*", handler)
        bot.run()

    def run_all(self):
        """Start all saved bots."""
        for bot in self.bots:
            threading.Thread(target=self._run_bot, args=(bot["token"],), daemon=True).start()
