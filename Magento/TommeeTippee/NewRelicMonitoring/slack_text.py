from decouple import config


def generate_slack_message(count_10: int, count_60: int) -> str:
    """
    Generate a Slack message with information about potential abusive activity.

    :param count_10: The count of instances of activity from a particular IP address in the last 10 minutes.
    :type count_10: int
    :param count_60: The count of instances of activity from the same IP address in the last 60 minutes.
    :type count_60: int
    :return: The generated Slack message containing the provided counts and instructions for investigation.
    :rtype: str
    """
    message = f"""There is a potential abuser on our {config("CUSTOMER_NAME", default="")} websites. In the last 10 minutes, there have been {count_10} instances of activity from a particular IP address, and {count_60} instances in the last 60 minutes from the same IP address. While I can't reveal the IP directly, you can find it on New Relic for investigation.
1. Log in to New Relic 
2. Go to Metrics & Events
3. Press Events
4. Event Type dropdown -> Log
5. Plot dropdown -> count(*)
6. Dimensions dropdown -> client_ip
Under the charts you will be able to find Client Ip and Count. Count must be sorted Descendent.
By default time interval in the upper right corner is set to 30 minutes. Play with it according to your needs.

Metrics & Events are available to Pin to the side menu from All Capabilities"""

    return message
