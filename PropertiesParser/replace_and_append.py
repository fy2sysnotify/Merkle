target_file = 'resource/email.properties'
source_file = 'dev_folder/email.properties'

with open(target_file) as file1:
    target_file_data = file1.read()
with open(source_file) as file2:
    file2data = file2.read()

target_dictionary = target_file_data.split('\n')
target_dictionary = list(filter(None, target_dictionary))
source_dictionary = file2data.split('\n')
source_dictionary = list(filter(None, source_dictionary))

for target_line in target_dictionary:
    target_split = target_line.split('=')
    target_key = target_split[0]
    target_value = target_split[1]
    for source_line in source_dictionary:
        source_split = source_line.split('=')
        source_key = source_split[0]
        source_value = source_split[1]
        if source_key == target_key and target_value != source_value:
            target_file_data = target_file_data.replace(target_line, source_line)

with open(target_file, 'w') as file3:
    file3.write(target_file_data)

target = './resource/email.properties'
source = './dev_folder/email.properties'

with open(target) as target_file:
    with open(source) as source_file:
        difference = set(source_file).difference(target_file)

difference.discard('\n')

with open(target, 'a+') as file_out:
    for line in difference:
        file_out.write(f'\n{line}')
