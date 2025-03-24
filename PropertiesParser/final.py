import os
import time
from jproperties import Properties

resource_folder = './dev_folder/'
target_folder = './resources/'

script_start_time = time.perf_counter()

configs = Properties()

for (root_source, dirs_source, files_source) in os.walk(resource_folder):
    for source_file in files_source:
        file_name_source = os.path.join(root_source, source_file)
        for (root_target, dirs_target, files_target) in os.walk(target_folder):
            for target_file in files_target:
                file_name_target = os.path.join(root_target, target_file)
                if (
                        target_file.endswith('.properties')
                        and source_file == target_file
                ):
                    with open(file_name_target, 'rb') as target_properties_file:
                        target_file_data = target_properties_file.read()
                        configs.load(target_properties_file)
                        target_list = configs.items()
                    with open(file_name_source, 'rb') as source_properties_file:
                        source_file_data = source_properties_file.read()
                        configs.load(source_properties_file)
                        source_list = configs.items()

                    for target_item in target_list:
                        target_key = target_item[0]
                        target_value = target_item[1].data
                        for source_item in source_list:
                            source_key = source_item[0]
                            source_value = source_item[1].data
                            if source_key == target_key and target_value != source_value:
                                target_file_data = target_file_data.replace(target_key, source_key)

                    with open(file_name_target, 'wb') as file3:
                        file3.write(target_file_data)

                    with open(file_name_target) as target:
                        with open(file_name_source) as source:
                            difference = set(source).difference(target)

                    difference.discard('\n')

                    with open(file_name_target, 'a+') as file_out:
                        for line in difference:
                            file_out.write(f'\n{line}')

                    print(f'preprocessed file is {target_file} and it was saved in {target_folder} folder')

script_finish_time = time.perf_counter()
print(f'Script execution time is {round(script_finish_time - script_start_time, 2)} seconds.')

print('I did my job')

terminate = False
while not terminate:
    user_input = input('type "exit" and press enter or close the console: ')
    if user_input == 'exit':
        terminate = True
