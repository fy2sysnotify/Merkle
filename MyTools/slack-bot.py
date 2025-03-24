import slack_sdk
from slack_sdk import WebClient
import os
from pathlib import Path

slack_token = os.getenv('SLACK_BOT')


def slack_post(slack_message):
    try:
        slack_channel = '#test'
        slack_client = slack_sdk.WebClient(token=slack_token)
        slack_client.chat_postMessage(channel=slack_channel, text=slack_message)
    except:
        pass


slack_post('This is a test')