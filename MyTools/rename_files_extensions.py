import os

for file_path in os.walk('../PropertiesParser/resources'):
    for list_of_items in file_path:
        for item in list_of_items:
            if item.endswith('.properties'):
                prefix, extension = os.path.splitext(item)
                os.rename(item, f'{prefix}.csv')
                print(item)
