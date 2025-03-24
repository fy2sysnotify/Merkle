import os
import time

resource_folder = './dev_folder/'
target_folder = './resources/'

script_start_time = time.perf_counter()


def merge_to_double_backslash(input_list):
    output_list = input_list[:1]
    for item in input_list[1:]:
        if output_list[-1].endswith('\\'):
            output_list[-1] += item
        else:
            output_list.append(item)

    return output_list


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
                    with open(file_name_target) as file1:
                        target_file_data = file1.read()
                    with open(file_name_source) as file2:
                        source_file_data = file2.read()

                    target_list = target_file_data.split('\n')
                    target_list = list(filter(None, target_list))
                    target_list = merge_to_double_backslash(target_list)
                    source_list = source_file_data.split('\n')
                    source_list = list(filter(None, source_list))
                    source_list = merge_to_double_backslash(source_list)

                    for target_item in target_list:
                        if '#' not in target_item:
                            target_split = target_item.split('=')
                            target_key = target_split[0]
                            target_value = target_split[1]
                            for source_item in source_list:
                                if '#' not in source_item:
                                    source_split = source_item.split('=')
                                    source_key = source_split[0]
                                    source_value = source_split[1]
                                    if source_key == target_key and target_value != source_value:
                                        target_file_data = target_file_data.replace(target_item, source_item)

                                        with open(file_name_target, 'w') as file3:
                                            file3.write(target_file_data)

                                        with open(file_name_target) as target:
                                            with open(file_name_source) as source:
                                                difference = set(source).difference(target)

                                        difference.discard('\n')

                                        with open(file_name_target, 'a+') as file_out:
                                            for line in difference:
                                                file_out.write(f'\n{line}')

                                        print(
                                            f'preprocessed file is {target_file} and it was saved in {target_folder} folder')

script_finish_time = time.perf_counter()
print(f'Script execution time is {round(script_finish_time - script_start_time, 2)} seconds.')

print('I did my job')

terminate = False
while not terminate:
    user_input = input('Type "exit" and press enter or close the console: ')
    if user_input == 'exit':
        terminate = True
