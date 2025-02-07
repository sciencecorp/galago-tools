from slack_sdk import WebClient
from dotenv import load_dotenv
import os 
import requests
from tools.base_server import ABCToolDriver

load_dotenv(
    dotenv_path=os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "..",
        ".env.local",
    )
)

class Messages(ABCToolDriver):
    def __init__(self) -> None:
        self.slack_channel: str = os.getenv("ACTIVE_CULTURE_CHANNEL") # type: ignore
        self.slack_token: str = os.getenv("WORKCELL_BOT_TOKEN") # type: ignore


    def slack_message(self, message: str, channel:str) -> None:
        try:
            client = WebClient(token=self.slack_token)
            if not self.slack_channel:
                # throw error
                raise Exception("No slack channel specified")
            client.chat_postMessage(channel=self.slack_channel, text=message)

        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Unable to post slack message to {self.slack_channel}"
            ) from e
    
    def send_email(self, message:str) -> None:
        return None
    
    