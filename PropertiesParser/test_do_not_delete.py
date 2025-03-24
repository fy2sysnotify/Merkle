import os
import shutil
import urllib3
from pathlib import Path
from datetime import datetime
from webdav3.client import Client as webdavClient
import constants


def create_folder(folder_name):
    os.mkdir(folder_name)


def download_webdav_folder(folder_name, source_url, username, password):
    options = {
        'webdav_hostname': source_url,
        'webdav_login': username,
        'webdav_password': password,
        'webdav_timeout': 300
    }
    webdav = webdavClient(options)
    webdav.verify = False
    urllib3.disable_warnings()
    webdav.download_directory(folder_name, folder_name)


def backup_folder(folder_name):
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    back_up_folder = f'BackupFolder_{current_time}'
    os.mkdir(back_up_folder)
    shutil.copytree(folder_name, back_up_folder, dirs_exist_ok=True, ignore=shutil.ignore_patterns('.history'))
    zip_archive = f'backupFolder_{current_time}'
    shutil.make_archive(back_up_folder, 'zip', zip_archive)
    shutil.rmtree(f'./{zip_archive}')


def remove_subfolder(folder_name, subfolder_name):
    dir_path = Path(folder_name, subfolder_name)
    if dir_path.exists() and dir_path.is_dir():
        shutil.rmtree(dir_path)


def merge_to_double_backslash(input_list):
    output_list = input_list[:1]
    for item in input_list[1:]:
        if output_list[-1].endswith('\\'):
            output_list[-1] += item
        else:
            output_list.append(item)
    return output_list


def merge_properties_files(resource_folder, target_folder):
    for (root_source, dirs_source, files_source) in os.walk(resource_folder):
        for source_file in files_source:
            if source_file.endswith('.properties'):
                merge_file(root_source, source_file, target_folder)


def merge_file(root_source, source_file, target_folder):
    file_name_source = os.path.join(root_source, source_file)
    for (root_target, dirs_target, files_target) in os.walk(target_folder):
        for target_file in files_target:
            if (
                    target_file.endswith('.properties')
                    and source_file == target_file
            ):
                merge_properties(file_name_source, os.path.join(root_target, target_file))


def merge_properties(file_name_source, file_name_target):
    target_list = read_file_to_list(file_name_target)
    source_list = read_file_to_list(file_name_source)
    target_list = merge_lists(target_list, source_list)
    write_list_to_file(target_list, file_name_target)


def read_file_to_list(file_name):
    file_data = Path(file_name).read_text()
    file_list = file_data.split('\n')
    file_list = list(filter(None, file_list))
    file_list = merge_to_double_backslash(file_list)
    return file_list


def merge_lists(target_list, source_list):
    def parse_item(item):
        if '#' not in item:
            item_key, item_value = item.split('=')
            return item_key, item_value

    target_list = list(filter(lambda x: '#' not in x, target_list))
    target_dict = dict(map(parse_item, target_list))
    source_list = list(filter(lambda x: '#' not in x, source_list))
    source_dict = dict(map(parse_item, source_list))

    for key in target_dict.keys():
        if key in source_dict:
            target_dict[key] = source_dict[key]

    return [f'{key}={value}' for key, value in target_dict.items()]


def write_list_to_file(file_list, file_name):
    file_data = '\n'.join(file_list)
    Path(file_name).write_text(file_data)


def main():
    folder_name = 'resources'
    create_folder(folder_name)
    source_url = 'https://someurl.com'
    username = constants.USERNAME
    password = constants.PASSWORD
    download_webdav_folder(folder_name, source_url, username, password)
    backup_folder(folder_name)
    remove_subfolder(folder_name, '.history')
    merge_properties_files('dev_folder', folder_name)


if __name__ == '__main__':
    main()
