import datetime

DT = (datetime.datetime.now() - datetime.timedelta(minutes=60)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

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
                'term_query': {
                    'fields': ['status'],
                    'operator': 'is',
                    'values': ['failed'],
                },
            },
        },
    },
    'select': '(hits.(data.(order_no, creation_date, status, total)))',
    'count': 200,
    'sorts': [{'field': 'creation_date', 'sort_order': 'desc'}]
}