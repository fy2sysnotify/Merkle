import os
import slack_sdk
from slack_sdk.errors import SlackApiError


def slack_post(slack_message):
    try:
        slack_channel = '#zumnorde-monitoring'
        slack_client = slack_sdk.WebClient(os.getenv('SLACK_BOT'))
        slack_client.chat_postMessage(channel=slack_channel, text=slack_message)
    except Exception as e:
        print(e)
        raise


def upload_to_slack(file_to_upload, slack_comment):
    try:
        slack_channel = '#zumnorde-monitoring'
        slack_client = slack_sdk.WebClient(token=os.getenv('SLACK_BOT'))
        slack_client.files_upload(
            channels=slack_channel,
            initial_comment=slack_comment,
            file=file_to_upload,
        )
    except SlackApiError as ex:
        print(f'Error uploading file: {ex}')
        raise
