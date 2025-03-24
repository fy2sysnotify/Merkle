from typing import Union


def count_all_client_ips(account_id_param: str, interval_value: Union[int, float], interval_unit: str) -> str:
    """
    Generates a NRQL query to count all client IPs within a specified time interval.

    :param str account_id_param: The account ID parameter.
    :param Union[int, float] interval_value: The value for the time interval.
    :param str interval_unit: The unit for the time interval (e.g., 'MINUTES', 'HOURS', 'DAYS').

    :return: The generated NRQL query.
    :rtype: str
    """
    query = f"""
    {{
      actor {{
        account(id: {account_id_param}) {{
          nrql(query: "SELECT count(*) FROM Log FACET client_ip WHERE request_user_agent NOT IN ('AfterShip Magento-2 Connector') SINCE {interval_value} {interval_unit} AGO TIMESERIES") {{
            results
          }}
        }}
      }}
    }}
    """
    return query


def count_client_ip(account_id_param: str, interval_value: Union[int, float], interval_unit: str,
                    client_ip: str) -> str:
    """
    Generates a NRQL query to count client IPs within a specified time interval.

    :param str account_id_param: The account ID parameter.
    :param Union[int, float] interval_value: The value for the time interval.
    :param str interval_unit: The unit for the time interval (e.g., 'MINUTES', 'HOURS', 'DAYS').
    :param str client_ip: The client IP address.

    :return: The generated NRQL query.
    :rtype: str
    """
    query = f"""
    {{
      actor {{
        account(id: {account_id_param}) {{
          nrql(query: "SELECT count(*) FROM Log FACET client_ip WHERE client_ip = '{client_ip}' SINCE {interval_value} {interval_unit} AGO TIMESERIES") {{
            results
          }}
        }}
      }}
    }}
    """
    return query
