from googleapiclient.discovery import build
import os

api_key = os.environ.get('YOUTUBE_API')

youtube = build('youtube', 'v3', developerKey=api_key)

request = youtube.channels().list(part='statistics', forUsername='kosyoyanev')
response = request.execute()

print(response)