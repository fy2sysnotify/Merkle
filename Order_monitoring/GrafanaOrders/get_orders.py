import os
import logging
import datetime
import requests
import pandas as pd
from client_creds_token import get_access_token

SCRIPT_NAME = 'order_count'
sites = ['ASDA']
DT = (datetime.datetime.now() - datetime.timedelta(minutes=125)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

# Configure logging
log_format = '%(levelname)s %(asctime)s - %(message)s'
SCRIPT_LOG_FILE = f'{SCRIPT_NAME}_{datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")}.log'
logging.basicConfig(filename=SCRIPT_LOG_FILE,
                    level=logging.DEBUG,
                    format=log_format)
logger = logging.getLogger()

# Headers for the API request
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {get_access_token(os.getenv("ASDA_CLIENT_ID"), os.getenv("ASDA_CLIENT_PASS"))}',
}

# JSON payload for the API request
json_data = {
    'query': {
        'filtered_query': {
            'filter': {
                'range_filter': {
                    'field': 'creation_date',
                    'from': DT,
                },
            },
            'query': {
                'match_all_query': {},
            },
        },
    },
    'select': '(**)',
}


# Helper function to log and print messages
def log_and_print(text):
    print(text)
    logger.info(text)


# Function to fetch the order count from the API
def get_order_count(site_id):
    url = f'https://george.com/s/{site_id}/dw/shop/v19_5/order_search'
    response = requests.post(url, headers=headers, json=json_data)

    if response.status_code != 200:
        response.raise_for_status()

    order_data = response.json()
    return order_data


# Initialize a list to store results for each site
results = []

# Loop through sites and fetch order counts
for site_id in sites:
    try:
        order_data = get_order_count(site_id)
        total_orders = order_data['count']
        hits = order_data.get('hits', [])

        # Process hits data into separate columns
        for hit in hits:
            data = hit.get('data', {})
            flattened_data = {f"data_{key}": value for key, value in data.items()}
            flattened_data['Site'] = site_id
            flattened_data['TotalOrders'] = total_orders
            results.append(flattened_data)

        log_and_print(f'{site_id} = {total_orders} orders fetched.')
    except Exception as e:
        log_and_print(f'Error for site {site_id}: {e}')
        results.append({'Site': site_id, 'Error': str(e)})

# Create a pandas DataFrame from the results
df = pd.DataFrame(results)

# Define the output Excel file name
excel_file = f'{SCRIPT_NAME}_results_{datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")}.xlsx'

# Export the DataFrame to an Excel file
df.to_excel(excel_file, index=False)
log_and_print(f'Results have been exported to {excel_file}')
