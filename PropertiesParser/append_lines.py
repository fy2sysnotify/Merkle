target = './resource/email.properties'
source = './dev_folder/email.properties'

with open(target) as target_file:
    with open(source) as source_file:
        difference = set(source_file).difference(target_file)

difference.discard('\n')

with open(target, 'a+') as file_out:
    for line in difference:
        file_out.write(f'\n{line}')
