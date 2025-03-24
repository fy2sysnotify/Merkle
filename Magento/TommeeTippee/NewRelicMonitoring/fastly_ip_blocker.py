import requests
from decouple import config

headers = {
    'Fastly-Key': config('FASTLY_API_TOKEN', default=''),
    'Accept': 'application/json',
}

params = {
    'direction': 'ascend',
    'page': '1',
    'per_page': '20',
    'sort': 'created',
}

response = requests.get(
    f'https://api.fastly.com/service/{config("FASTLY_SERVICE_ID", default="")}/acl/U7nyX4s8kDMoD2x6B515i7/entries',
    params=params,
    headers=headers,
)

print(response.json())
