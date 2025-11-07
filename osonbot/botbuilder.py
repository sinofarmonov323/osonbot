import threading
from jsonbot import JsonBot

class BotBuilder:
    """
    Run multiple Telegram bots simultaneously using JsonBot.
    """
    
    def __init__(self):
        self.bots = {}
    
    def add_bot(self, token: str, commands: dict):
        """
        Add a bot with its commands
        
        Args:
            token: Bot token from @BotFather
            commands: Dictionary of commands
                     e.g., {
                         "/start": {"response": "Hello {first_name}!"},
                         "/help": {"response": "Need help?", "parse_mode": "MarkdownV2"}
                     }
        """
        if token in self.bots:
            return False
        
        bot = JsonBot(token, commands)
        
        thread = threading.Thread(target=bot.run, daemon=True)
        thread.start()
        
        self.bots[token] = {
            'bot': bot,
            'thread': thread
        }
        
        return True
    
    def remove_bot(self, token: str):
        if token in self.bots:
            del self.bots[token]
            return True
        return False
    
    def get_active_bots(self):
        return list(self.bots.keys())
    
    def bot_exists(self, token: str):
        return token in self.bots
