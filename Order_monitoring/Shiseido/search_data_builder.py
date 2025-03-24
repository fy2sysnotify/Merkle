from typing import Dict


def build_search_data(dt: str) -> Dict:
    """
    Build search data based on the provided datetime.

    :param: dt (str): Datetime string in the format '%Y-%m-%dT%H:%M:%S.000Z'.
    :return (dict): Constructed search data.
    """
    return {
        "query": {
            "filtered_query": {
                "filter": {
                    "range_filter": {
                        "field": "creation_date",
                        "from": dt
                    }
                },
                "query": {
                    "match_all_query": {}
                }
            }
        },
        "select": "(total)"
    }
