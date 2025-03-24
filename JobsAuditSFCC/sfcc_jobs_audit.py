import os
import time
from pathlib import Path
from datetime import datetime
import zipfile
import filecmp
import difflib
import httpx
from decouple import config
from set_email import send_email
from client_creds_token import get_access_token

business_email = config('BUSINESS_EMAIL', default='')
sfcc_pass = config('SFCC_PASS', default='')
pig_name = 'production_asda'
job_trigger_url = 'https://production-asda-ecommera.demandware.net/s/-/dw/data/v21_10/jobs/sfcc-site-archive-export/executions'
bm = 'https://production-asda-ecommera.demandware.net/on/demandware.store/Sites-Site'
instance_string = 'production-asda-ecommera.demandware.net'
export_zip_name = f'jobs_audit_{datetime.now().strftime("%Y%m%d")}.zip'
parent_folder = export_zip_name.removesuffix('.zip')
report_filename = f'{pig_name}_jobs_audit_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.html'
yesterday_file = 'ASDA_PROD/jobs.xml'
today_file = f'{export_zip_name.removesuffix(".zip")}/jobs.xml'
access_token = get_access_token()
export_filename = f'jobs_audit_{datetime.now().strftime("%Y%m%d")}'
url = f'https://{instance_string}/on/demandware.servlet/webdav/Sites/Impex/src/instance/{export_zip_name}'


def trigger_sfcc_site_import_archive_job():
    payload = {
        "data_units": {
            "global_data": {
                "job_schedules": True
            }
        },
        "export_file": export_filename,
        "overwrite_export_file": True
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token
    }

    try:
        with httpx.Client() as client:
            run_job_response = client.post(job_trigger_url, headers=headers, json=payload)
            run_job_response.raise_for_status()
            return run_job_response.json()
    except httpx.HTTPStatusError as e:
        print('POST request failed with status code:', e.response.status_code)
    except Exception as e:
        print('An error occurred:', str(e))
    return None


response = trigger_sfcc_site_import_archive_job()

if response:
    print("Response:", response)

time.sleep(10)


def download_file(download_url, instance_username, instance_password):
    with httpx.Client(auth=(instance_username, instance_password)) as client:
        download_file_response = client.get(download_url)
        if download_file_response.status_code == 200:
            file_name = download_url.split("/")[-1]
            with open(file_name, "wb") as file:
                file.write(download_file_response.content)
            print(f'"{file_name}" downloaded successfully.')
            return file_name  # Return the downloaded file's name
        else:
            print('Failed to download the file.')
            return None


def remove_remote_file(remote_filename, instance_username, instance_password):
    remote_file_url = f'https://{instance_string}/on/demandware.servlet/webdav/Sites/Impex/src/instance/{remote_filename}'

    with httpx.Client(auth=(instance_username, instance_password)) as client:
        delete_file_response = client.delete(remote_file_url)

        if delete_file_response.status_code == 204:
            print(f'Successfully deleted remote file "{remote_filename}"')
        else:
            print(f'Failed to delete remote file "{remote_filename}" with status code:', delete_file_response.status_code)


downloaded_file = download_file(url, business_email, sfcc_pass)

if downloaded_file:
    remove_remote_file(downloaded_file, business_email, sfcc_pass)


def unzip_file(filename):
    try:
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall()
        print(f'Successfully unzipped "{filename}"')
    except zipfile.BadZipFile:
        print(f'Error: "{filename}" is not a valid ZIP file')
    except FileNotFoundError:
        print(f'Error: "{filename}" not found')


unzip_file(export_zip_name)


def remove_local_file(filename):
    try:
        os.remove(filename)
        print(f'Successfully removed "{filename}"')
    except FileNotFoundError:
        print(f'Error: "{filename}" not found')
    except PermissionError:
        print(f'Error: Permission denied to remove "{filename}"')


remove_local_file(export_zip_name)


def files_are_identical(file_path_old, file_path_new):
    return filecmp.cmp(file_path_old, file_path_new)


def generate_difference_report(file_path_old, file_path_new):
    old_file_lines = open(file_path_old, encoding='utf-8').readlines()
    new_file_lines = open(file_path_new, encoding='utf-8').readlines()
    difference = difflib.HtmlDiff().make_file(old_file_lines, new_file_lines, file_path_old, file_path_new)
    with open(report_filename, 'w', encoding='utf-8') as difference_report:
        difference_report.write(difference)


def generate_html_table(column_data):
    column_names = [column[0] for column in column_data]
    column_values = [column[1] for column in column_data]

    table_html = """
    <table style="border-collapse: collapse; font-family: Arial, sans-serif;">
        <thead style="background-color: #f2f2f2;">
            <tr>
    """

    for column_name in column_names:
        table_html += "<th style='border: 2px solid #000000; padding: 12px;'>{}</th>\n".format(column_name)

    table_html += "</tr>\n</thead>\n<tbody>\n<tr>\n"

    for i, column_value in enumerate(column_values):
        cell_style = "border: 2px solid #000000; padding: 12px;"

        if i == 0:
            masked_value = column_value
            table_html += "<td style='{}'><a href='{}' style='font-weight: bold;'>{}</a></td>\n".format(
                cell_style, column_value, masked_value
            )
        else:
            if column_value == "NO":
                cell_style += " color: green; font-weight: bold;"
            elif column_value == "YES":
                cell_style += " color: red; font-weight: bold;"
            table_html += "<td style='{}'>{}</td>\n".format(cell_style, column_value)

    table_html += "</tr>\n</tbody>\n</table>"

    return table_html


if files_are_identical(yesterday_file, today_file):
    print('The files are identical.')
    data_for_columns = [
        ('PIG Instance', bm),
        ('Difference', 'NO')
    ]

    html_table = generate_html_table(data_for_columns)

    send_email(
        email_recipient='konstantin.yanev@merkle.com',
        email_subject='jobs_difference_audit',
        email_message='Hi Team, this is the jobs audit report for today.\n'
                      'It compares sfcc jobs structure and content between\n'
                      'today and yesterday on all major Primary Instance Groups.\n',
        html_table=html_table
    )

else:
    print('There is a difference between the files.')
    generate_difference_report(yesterday_file, today_file)

    data_for_columns = [
        ('PIG Instance', bm),
        ('Difference', 'YES')
    ]

    html_table = generate_html_table(data_for_columns)

    send_email(
        email_recipient='konstantin.yanev@merkle.com',
        email_subject='jobs_difference_audit',
        email_message='Hi Team, this is the jobs audit report for today.\n'
                      'It compares sfcc jobs structure and content between\n'
                      'today and yesterday on all major Primary Instance Groups.\n'
                      'Differences between jobs can be found in the attachments.'
                      'With any difference in jobs proceed as per wiki scenarios.',
        html_table=html_table,
        attachment_location=str(Path.cwd() / report_filename)
    )
