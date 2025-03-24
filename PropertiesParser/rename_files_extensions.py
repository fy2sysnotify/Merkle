from pathlib import Path


def rename_extensions(old_extension=None, new_extension=None, folder_path=None):

    path = Path(folder_path)

    for file in path.iterdir():
        if file.is_file() and file.suffix in [old_extension]:
            file.rename(file.with_suffix(new_extension))


rename_extensions(old_extension='.properties', new_extension='.csv', folder_path='./resources')
