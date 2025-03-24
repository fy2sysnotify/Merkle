import os

resource_folder = 'dev_folder'

for (root_source, dirs_source, files_source) in os.walk(resource_folder):
    for source_file in files_source:
        for (root_target, dirs_target, files_target) in os.walk('.'):
            for target_file in files_target:
                if target_file.endswith('.properties'):
                    if source_file == target_file:
                        print(True, f'{source_file} = {target_file}')
                    else:
                        print(False, f'{source_file} not equal to {target_file}')
