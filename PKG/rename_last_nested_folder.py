import os


def rename_deepest_nested_folder(base_folder, target_folder_name):
    """
    Recursively renames the deepest nested folder in the given base folder to the specified target folder name.

    :param str base_folder: The path to the base folder containing nested subdirectories.
    :param str target_folder_name: The desired name for the deepest nested folder.

    :return: None
    :rtype: NoneType

    :raises FileNotFoundError: If the specified base folder does not exist.
    :raises PermissionError: If the user does not have permission to rename the folders.

    This function traverses the directory structure starting from the provided base folder.
    It identifies the deepest nested folder and renames it to the specified target folder name.
    The renaming process is done recursively, ensuring that the deepest nested folder is accurately identified.

    Example usage:
    ```python
    jcr_root_path = "./jcr_root"
    rename_deepest_nested_folder(jcr_root_path, "world_of_light")
    ```

         :note::
        - If multiple folders have the same depth as the deepest nested folder, the function renames the first one encountered.
        - It prints information about the renaming process, including the path to the deepest nested folder, old name, and new name.
    """
    # Get the list of subdirectories in the base_folder
    subdirectories = [d for d in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, d))]

    # Check if there are any subdirectories
    if subdirectories:
        # Recursively call the function for each subdirectory
        for subdirectory in subdirectories:
            subdirectory_path = os.path.join(base_folder, subdirectory)
            if os.path.isdir(subdirectory_path):
                rename_deepest_nested_folder(subdirectory_path, target_folder_name)

    # Check if this is the deepest nested folder
    if not subdirectories:
        # Print information and rename the current base folder to the target folder name
        old_name = os.path.basename(base_folder)
        new_name = target_folder_name
        os.rename(base_folder, os.path.join(os.path.dirname(base_folder), new_name))

        # Print information about the renaming process
        print(f"Path to deepest nested folder: {base_folder}")
        print(f"Old name: {old_name}")
        print(f"New name: {new_name}")
        print("")


# Example usage:
jcr_root_path = "./jcr_root"
rename_deepest_nested_folder(jcr_root_path, "world_of_light")
