import httpx

class Bot:
    def __init__(self, token):
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.handlers = {}

    def when(self, condition: str, text: str, once: bool = False):
        if condition:
            self.handlers[condition] = {"text": text, "once": once}
    
    def get_updates(self, offset: int):
        return httpx.get(self.api_url+"getUpdates", params={'offset': offset}).json()
    
    def send_message(self, chat_id, text: str):
        httpx.get(self.api_url+"sendMessage", params={'chat_id': chat_id, "text": text})
    
    def process_messages(self, message):
        text = message.get("text", "")
        chat_id = message['chat']['id']
        handled = self.handlers.get(text) or self.handlers.get("*")
        
        if handled:
            self.send_message(chat_id, handled['text'])
    
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
