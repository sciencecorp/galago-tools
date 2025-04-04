from slack_sdk import WebClient
import json
import os 
import logging
import requests
from typing import Any
from tools.app_config import Config
from typing import Optional 
import time 

slack_active = True

class Slack():
    def __init__(self, config:Config) -> None:
        self.client = WebClient(token="")

    def slack_message(self, message:Optional[str], recipient:str) -> None:
        try:
            self.client.chat_postMessage(
                channel=recipient,
                text=message
            )
        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Unable to post slack message to {recipient}"
            ) from e

    def slack_block_message(self, message:Any,attachments:Any, recipient:str) -> None:
        try:
            self.client.chat_postMessage(
                channel=recipient,
                text=message,
                attachments=attachments
            )
        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Unable to post slack message to {recipient}"
            ) from e
        
    def create_alert_message(self,title:str, workcell:str, tool:str, protocol:str, error:str) -> Any:
        template_path = os.path.join(os.path.dirname(__file__),"slack_templates","error_template.json")
        with open(template_path) as f:
            template_json = json.load(f)
        
        template_string = json.dumps(template_json)
        template_string = template_string.replace("<title_holder>", title)
        template_string = template_string.replace("<workcell_holder>", workcell)

        timestamp = str(time.strftime("%Y-%m-%d %H:%M:%S"))
        template_string = template_string.replace("<time_holder>", timestamp)
        template_string = template_string.replace('"<time_holder_int>"', str(time.time()))
        template_string = template_string.replace("<tool_holder>", tool)
        template_string = template_string.replace("<protocol_holder>", protocol)
        template_string = template_string.replace("<error_placeholder>", error)
        template_string = template_string.replace("<color_placeholder>", "#FF0000")

        return json.loads(template_string)
    
    def update_alert(self, workcell:str, tool:str, protocol:str, error:str, channel_id:str,status_update:str, message_id:str) -> None:
        msg =self.create_alert_message(title=status_update, workcell=workcell,tool=tool,protocol=protocol,error=error)
        self.client.chat_update(channel=channel_id,ts=message_id,text="",attachments=msg)
    
    def clear_last_error(self, channel_id:str) -> None:
        last_messages = self.get_last_messages(channel_id=channel_id)
        for msg in last_messages:
            #print(f"Message is {msg}")
            if msg:
                if 'attachments' in msg:
                    msg_resp = msg['attachments'][0]
                    if 'title' in msg_resp:
                        print(f"Title is {msg_resp['title']}")
                        if msg_resp['title'] == 'Workcell has errored!':
                            msg_resp['title'] = 'Error is resolved!'
                            msg_resp['color'] = '#36a64f'
                        #If the last message is not in error state, exit.
                        else:
                            continue
                    if 'fields' in msg_resp:
                        new_fields = msg_resp['fields']
                        for i in range(len(msg_resp['fields'])):
                            field = msg_resp['fields'][i]
                            if field['title'] == 'Last Updated':
                                new_fields[i]['value'] = str(time.strftime("%Y-%m-%d %H:%M:%S"))
                        msg_resp['fields'] = new_fields
                    message_id = msg['ts']
                    self.client.chat_update(channel=channel_id,ts=message_id,text="",attachments=[msg_resp])

    def send_alert_slack(self, workcell:str, tool:str, protocol:str, error:str, channel_id:str) -> None:
        message = self.create_alert_message(title="Workcell has errored!", workcell=workcell, tool=tool, protocol=protocol, error=error)
        self.slack_block_message(message="Galago Alert",attachments=message,recipient=channel_id )
    
    def retrieve_message(self, message_id:str, channel_id:str)-> Any:
        try:
            result = self.client.conversations_history(
                channel=channel_id,
                inclusive=True,
                oldest=message_id,
                limit=1
            )
            print("Raw message is"+ str(result))
            return result
        except Exception as e:
            logging.error(f"Error: {e}")

    def get_last_messages(self, channel_id:str) -> Any:
        try:
            response = self.client.conversations_history(channel=channel_id, limit=5)
            if response['ok'] and response['messages']:
                last_messages = response['messages']
                #print(f"Last 5 messages {last_messages}")
                return last_messages
            else:
                return None
        except Exception as e:
            logging.error(f"Error fetching messages from Slack: {e}")
            return None
