import zipfile
import os
import shutil


def unzip_file(zip_path, extract_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)


def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"Deleted '{file_path}'.")
    except Exception as delete_error:
        print(f"Error deleting '{file_path}': {delete_error}")


def rename_deepest_nested_folder(base_folder, target_folder_name):
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


def rename_last_nested_folder(base_folder, target_folder_name):
    # Get the list of subdirectories in the base_folder
    subdirectories = [d for d in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, d))]

    # Check if there are any subdirectories
    if subdirectories:
        # Get the last subdirectory
        last_subdirectory = subdirectories[-1]

        # Create the new path with the renamed folder
        new_path = os.path.join(base_folder, target_folder_name)

        # Rename the last subdirectory
        os.rename(os.path.join(base_folder, last_subdirectory), new_path)

        print(f"The last nested folder in {base_folder} has been renamed to '{target_folder_name}'.")
    else:
        print(f"No subdirectories found in {base_folder}.")


def create_zip_from_folder(folder_path, original_zip_name):
    with zipfile.ZipFile(original_zip_name, 'w') as new_zip:
        for root, _, files in os.walk(folder_path):
            rel_path = os.path.relpath(root, folder_path)
            for file in files:
                file_path = os.path.join(root, file)

                # Exclude files with ".zip" or ".py" extensions from being added to the new archive
                if not (file_path.endswith(original_zip_name) or file_path.endswith(".py")):
                    arcname = os.path.join(rel_path, file)
                    new_zip.write(file_path, arcname=arcname)


def delete_all_folders_in_current_directory() -> None:
    # Get the current directory
    current_directory: str = os.getcwd()

    # List all items in the current directory
    all_items: list = os.listdir(current_directory)

    # Iterate through each item and remove only folders
    for item in all_items:
        item_path: str = os.path.join(current_directory, item)

        # Check if the item is a directory
        if os.path.isdir(item_path):
            # Print the name of the deleted folder
            print(f"Deleting folder: {item}")

            # Remove the directory and its contents
            shutil.rmtree(item_path)

    print("All folders in the current directory have been deleted.")


def main():
    zip_file_name = "poc-singapore.zip"
    current_folder = os.getcwd()
    zip_file_path = os.path.join(current_folder, zip_file_name)
    extraction_path = current_folder

    try:
        # Unzip the file
        unzip_file(zip_file_path, extraction_path)
        print(f"Successfully extracted '{zip_file_name}' to '{extraction_path}'.")

        # Delete all files with the .zip extension, excluding the original zip file
        for file in os.listdir(current_folder):
            if file.endswith(".zip") and file != zip_file_name:
                delete_file(os.path.join(current_folder, file))

        jcr_root_path = "./jcr_root"
        rename_deepest_nested_folder(jcr_root_path, "world_of_light")

        # Create a new zip file with the extracted contents
        create_zip_from_folder(extraction_path, zip_file_name)
        print(f"Created a new zip file '{zip_file_name}' with the extracted contents.")

        # Call the function to delete folders in the current directory
        delete_all_folders_in_current_directory()

    except Exception as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
