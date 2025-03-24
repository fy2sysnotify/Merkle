from order_details_processor import Config, SlackNotifier, OrderMonitor
import constants as const


def main() -> None:
    """
    Main function to set up the order monitoring process for the Clarins BNL orders.

    This function configures the necessary components, including the script name, Slack
    channel, and orders URL. It then creates instances of the SlackNotifier and OrderMonitor
    classes and starts the order monitoring process.

    Returns:
        None
    """
    # Script name for tracking purposes
    script_name: str = 'clarins_check_orders_de'

    # Slack channel where order updates will be posted
    slack_channel: str = '#orders-monitor-clarins'

    # Constructing the URL to fetch orders for Clarins BNL from a constants file
    orders_url: str = f"{const.clarins_orders_m3}clarinsde"

    # Set the script name in the Config class for tracking purposes
    Config.set_script_name(script_name)

    # Dictionary to hold instances of Clarins BNL with corresponding ID
    clarins_instances: dict[str, int] = {'clarinsde': 2}

    # Initialize the SlackNotifier with the token from Config and the Slack channel
    slack_notifier: SlackNotifier = SlackNotifier(Config.SLACK_TOKEN, slack_channel)

    # Initialize the OrderMonitor with necessary components, including clarins instances and Slack notifier
    monitor: OrderMonitor = OrderMonitor(clarins_instances, slack_notifier, orders_url)

    # Run the order monitoring process, which continuously checks for order updates
    monitor.run()


if __name__ == '__main__':
    # Execute the main function when the script is called directly
    main()
