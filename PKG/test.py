import zipfile
import os
from pathlib import Path


def delete_and_unzip_file(zip_path, extract_path):
    # Extract the contents of the zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    try:
        # Delete the original zip file
        os.remove(zip_path)
        print(f"Deleted '{zip_path}'.")
    except Exception as delete_error:
        print(f"Error deleting '{zip_path}': {delete_error}")


def rename_deepest_nested_folder(base_folder, target_folder_name):
    # Get the list of subdirectories in the base_folder
    subdirectories = [d for d in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, d))]

    # Iterate until the deepest nested folder is found
    while subdirectories:
        subdirectory = subdirectories[0]
        subdirectory_path = os.path.join(base_folder, subdirectory)
        base_folder = subdirectory_path
        subdirectories = [d for d in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, d))]

    # Rename the deepest nested folder
    old_name = os.path.basename(base_folder)
    new_name = target_folder_name
    os.rename(base_folder, os.path.join(os.path.dirname(base_folder), new_name))

    # Print information about the renaming process
    print(f"Path to deepest nested folder: {base_folder}")
    print(f"Old name: {old_name}")
    print(f"New name: {new_name}\n")


def create_zip_from_folder(folder_path, original_zip_name):
    # Create a new zip file with the extracted contents
    with zipfile.ZipFile(original_zip_name, 'w') as new_zip:
        for root, _, files in os.walk(folder_path):
            rel_path = os.path.relpath(root, folder_path)
            for file in files:
                file_path = os.path.join(root, file)

                # Exclude files with ".zip" or ".py" extensions from being added to the new archive
                if not file_path.endswith((original_zip_name, ".py")):
                    arcname = os.path.join(rel_path, file)
                    new_zip.write(file_path, arcname=arcname)


def main():
    # Set up file paths and names
    zip_file_name = "poc-singapore.zip"
    current_folder = Path.cwd()
    zip_file_path = current_folder / zip_file_name
    extraction_path = current_folder

    try:
        # Unzip the file
        delete_and_unzip_file(zip_file_path, extraction_path)
        print(f"Successfully extracted '{zip_file_name}' to '{extraction_path}'.")

        # Delete all files with the .zip extension, excluding the original zip file
        for file in current_folder.glob("*.zip"):
            if file.name != zip_file_name:
                delete_and_unzip_file(file, current_folder)

        # Set up path to the deepest nested folder
        jcr_root_path = current_folder / "jcr_root"
        # Rename the deepest nested folder
        rename_deepest_nested_folder(jcr_root_path, "world_of_light")

        # Create a new zip file with the extracted contents
        create_zip_from_folder(extraction_path, zip_file_name)
        print(f"Created a new zip file '{zip_file_name}' with the extracted contents.")

    except Exception as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
