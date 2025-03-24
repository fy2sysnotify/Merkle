import os
from typing import Union, Optional
import slack_sdk
from slack_sdk.errors import SlackApiError


def slack_post(slack_channel: str, slack_message: str) -> Optional[None]:
    """
    Posts a message to the specified Slack channel.

    Args:
        slack_channel (str): The name of the channel to send the message to. It must start with #.
        slack_message (str): The message to post to the Slack channel.

    Raises:
        SlackApiError: If an error occurs while sending the message.

    Returns:
        None if the message was posted successfully.
    """

    try:
        slack_client = slack_sdk.WebClient(os.getenv('SLACK_BOT'))
        slack_client.chat_postMessage(channel=slack_channel, text=slack_message)
    except SlackApiError as e:
        print(f'Error sending message: {e}')
        raise


def upload_to_slack(slack_channel: str, file_to_upload: Union[str, bytes], slack_comment: str) -> Optional[None]:
    """
    Uploads a file to the specified Slack channel.

    Args:
        slack_channel (str): The name of the channel to upload the file to. It must start with #.
        file_to_upload (Union[str, bytes]): The file to upload. Can be a file path string or a bytes object.
        slack_comment (str): A comment to include with the uploaded file.

    Raises:
        SlackApiError: If an error occurs while uploading the file.

    Returns:
        None if the file was uploaded successfully.
    """

    try:
        slack_client = slack_sdk.WebClient(token=os.getenv('SLACK_BOT'))
        # Don't use files_upload_v2 method!!!
        slack_client.files_upload(
            channels=slack_channel,
            initial_comment=slack_comment,
            file=file_to_upload,
        )
    except SlackApiError as ex:
        print(f'Error uploading file: {ex}')
        raise
