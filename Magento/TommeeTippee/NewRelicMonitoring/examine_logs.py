import httpx
from decouple import config
from generate_nrql_query import count_all_client_ips, count_client_ip
from slack_messaging import slack_post, upload_to_slack
from slack_text import generate_slack_message

url = config('GRAPH_QL_API', default='')

account_id = config('ACCOUNT_ID', default='')

payload = {'query': count_all_client_ips(account_id, 10, 'MINUTES')}
headers = {
    'Api-Key': config('USER_API_KEY', default='')
}

with httpx.Client() as client:
    response = client.post(url, headers=headers, json=payload)

    # Convert response to dictionary
    response_dict = response.json()

    results = response_dict['data']['actor']['account']['nrql']['results']

    # Dictionary to accumulate counts for each IP
    ip_counts_10 = {}

    for result in results:
        client_ip = result['client_ip']
        count_10 = result['count']
        # Accumulate count for each IP
        if client_ip in ip_counts_10:
            ip_counts_10[client_ip] += count_10
        else:
            ip_counts_10[client_ip] = count_10

    # Print accumulated counts for each IP
    for ip, count_10 in ip_counts_10.items():
        if count_10 > 600:
            print("Client IP:", ip)
            print("Count for last 10 minutes:", count_10)
            payload = {'query': count_client_ip(account_id, 60, 'MINUTES', ip)}
            headers = {
                'Api-Key': config('USER_API_KEY', default='')
            }

            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=payload)

                # Convert response to dictionary
                response_dict = response.json()

                results = response_dict['data']['actor']['account']['nrql']['results']

                # Dictionary to accumulate counts for each IP
                ip_counts_60 = {}

                for result in results:
                    client_ip = result['client_ip']
                    count_60 = result['count']
                    # Accumulate count for each IP
                    if client_ip in ip_counts_60:
                        ip_counts_60[client_ip] += count_60
                    else:
                        ip_counts_60[client_ip] = count_60

                # Print accumulated counts for each IP
                for ip, count_60 in ip_counts_60.items():
                    print("Client IP:", ip)
                    print("Count for last 1 hour:", count_60)
                    try:
                        upload_to_slack(
                            slack_channel='#testes',
                            file_to_upload='nr_me.jpg',
                            slack_comment=generate_slack_message(count_10, count_60)
                        )
                    except Exception as e:
                        slack_post(
                            slack_channel='#testes',
                            slack_message=generate_slack_message(count_10, count_60)
                        )
