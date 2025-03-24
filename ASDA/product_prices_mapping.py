import xml.etree.ElementTree as ET
import time

# Start the timer to measure script performance
start_time = time.perf_counter()


# Function to parse an XML file, handling potential namespaces
def parse_xml_with_namespace(filename):
    """
    Parse an XML file and detect any namespaces if present.

    Args:
        filename (str): The XML file to parse.

    Returns:
        tuple: The root element of the XML and a dictionary of namespaces (if any).
    """
    tree = ET.parse(filename)  # Parse the XML file into an ElementTree object
    root = tree.getroot()  # Get the root element of the XML document

    # Check if there is a namespace defined in the root tag
    # Example of root.tag with namespace: '{http://example.com/ns}root'
    # We strip the '{http://example.com/ns}' part and map it to the prefix 'ns'
    namespaces = {'ns': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}

    return root, namespaces  # Return the root element and the namespace dictionary


# Parse the two XML files (list-prices and sale-prices) with potential namespace handling
list_prices_root, list_prices_ns = parse_xml_with_namespace('list-prices.xml')
sale_prices_root, sale_prices_ns = parse_xml_with_namespace('sale-prices.xml')


# Function to build a dictionary mapping product IDs to prices
def build_price_dict(root, namespaces, xml_name):
    """
    Build a dictionary mapping product IDs to prices from an XML structure.

    Args:
        root (Element): The root element of the XML document.
        namespaces (dict): A dictionary of namespaces (if applicable).
        xml_name (str): Name of the XML file (used for logging purposes).

    Returns:
        dict: A dictionary mapping product IDs to their corresponding prices.
    """
    price_dict = {}  # Initialize an empty dictionary to store prices

    # Define the XPath query for price-table elements, using namespace if present
    xpath_query = ".//{}price-table".format('ns:' if namespaces else '')

    # Iterate over all price-table elements in the XML file
    for price_table in root.findall(xpath_query, namespaces):
        # Extract the product ID from the price-table element's attribute
        product_id = price_table.get('product-id')

        # Find the amount element within the price-table, using namespace if present
        amount = price_table.find(".//{}amount".format('ns:' if namespaces else ''), namespaces)

        # Debugging: Log the extraction of product ID
        if product_id:
            print(f"Extracting {product_id} from {xml_name}")

        # If both product_id and amount are present, store them in the dictionary
        if product_id and amount is not None:
            price_dict[product_id] = amount.text
        else:
            # Log a warning if data is missing for the product ID or if amount is not found
            print(f"Warning: Missing data for product-id in {xml_name} or amount not found.")

    return price_dict  # Return the dictionary containing the product IDs and their prices


# Build dictionaries for list prices and sale prices
list_prices_dict = build_price_dict(list_prices_root, list_prices_ns, "list-prices.xml")
sale_prices_dict = build_price_dict(sale_prices_root, sale_prices_ns, "sale-prices.xml")

# Open input and output files (ensure the input file exists and contains product IDs)
with open('1_2', 'r', encoding='utf-8') as infile, open('1_3', 'w', encoding='utf-8') as outfile:
    # Process each line of the input file (each line represents a product ID)
    for line in infile:
        product_id = line.strip()  # Remove any leading/trailing whitespace (newlines, etc.)

        # Look up the prices for this product ID in the previously built dictionaries
        list_price = list_prices_dict.get(product_id)
        sale_price = sale_prices_dict.get(product_id)

        # Debugging: Print the product ID and the retrieved prices (list and sale)
        print(f"Looking up {product_id}: List price = {list_price}, Sale price = {sale_price}")

        # Only write to the output file if a list price is found (list_price is not None)
        if list_price:
            # Write the product ID, list price, and sale price (if available) to the output file
            outfile.write(f"{product_id},{list_price},{sale_price}\n")

# Stop the timer to measure the time taken for the entire script to execute
end_time = time.perf_counter()

# Print the total time taken for the script to complete
print(f"Script completed in {end_time - start_time:0.4f} seconds")
