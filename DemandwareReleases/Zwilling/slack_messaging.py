import os
from typing import Union
import slack_sdk
from slack_sdk.errors import SlackApiError


def slack_post(slack_message: str, slack_channel: str = '#drv-zwilling-ods'):
    """
    Posts a message to the Slack channel specified in the function.

    :param: slack_channel: Channel name to send the message to. It must start with #
    :param: slack_message: The message to post to the Slack channel.
    :return: None if the message was posted successfully, or an Exception object if an error occurred.
    """
    try:
        slack_client = slack_sdk.WebClient(os.getenv('SLACK_BOT'))
        slack_client.chat_postMessage(text=slack_message, channel=slack_channel)
    except SlackApiError as e:
        print(f'Error sending message: {e}')
        raise


def upload_to_slack(slack_channel: str, file_to_upload: Union[str, bytes], slack_comment: str):
    """
    Uploads a file to the Slack channel specified in the function.

    :param: slack_channel: Channel name to send the message to. It must start with #
    :param: file_to_upload: The file to upload. Can be a file path string or a bytes object.
    :param: slack_comment: A comment to include with the uploaded file.
    :return: None if the file was uploaded successfully, or a SlackApiError object if an error occurred.
    """
    try:
        slack_client = slack_sdk.WebClient(token=os.getenv('SLACK_BOT'))
        slack_client.files_upload(
            channels=slack_channel,
            initial_comment=slack_comment,
            file=file_to_upload,
        )
    except SlackApiError as ex:
        print(f'Error uploading file: {ex}')
        raise
