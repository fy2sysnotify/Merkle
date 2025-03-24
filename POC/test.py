import xmltodict
from bs4 import BeautifulSoup

# Load XML data as a dictionary
with open('.content.xml', encoding='utf-8') as xml_file:
    data_dict = xmltodict.parse(xml_file.read())

# Access the specific key 'gc08_teasercontainer_248922064'
specific_key_data = data_dict['jcr:root']['jcr:content']['parsys']['gc08_teasercontainer_248922064']

# Access the 'cell1Component-gc11' under the specific key
cell1_component_data = specific_key_data['cell1Component-gc11']

# Extract the HTML content from the 'title' attribute
title_html = cell1_component_data['@title']

# Use BeautifulSoup to parse the HTML
soup = BeautifulSoup(title_html, 'html.parser')

# Find all text nodes and replace their contents
for text_node in soup.find_all(text=True):
    text_node.replace_with("THIS IS MY WAY")

# Update the 'title' attribute with the modified HTML
cell1_component_data['@title'] = str(soup)

# Convert the entire modified dictionary back to XML
modified_xml = xmltodict.unparse(data_dict, pretty=True)

# Save the modified XML to a new file
with open('modified_content.xml', 'w', encoding='utf-8') as modified_file:
    modified_file.write(modified_xml)

print("Modified XML saved to 'modified_content.xml'")
