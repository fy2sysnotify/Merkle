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
from my_logger import configure_logger


class SFCCJobExporter:
    def __init__(self):
        self.logger = configure_logger(script_name=Path(__file__).stem)
        self.business_email = config('BUSINESS_EMAIL', default='')
        self.sfcc_pass = config('SFCC_PASS', default='')
        self.pig_name = 'production_asda'
        self.pig_instance = 'ASDA_PROD'
        self.job_trigger_url = 'https://production-asda-ecommera.demandware.net/s/-/dw/data/v21_10/jobs/sfcc-site-archive-export/executions'
        self.bm = 'https://production-asda-ecommera.demandware.net/on/demandware.store/Sites-Site'
        self.instance_string = 'production-asda-ecommera.demandware.net'
        self.export_zip_name = f'jobs_audit_{datetime.now().strftime("%Y%m%d")}.zip'
        self.parent_folder = self.export_zip_name.removesuffix('.zip')
        self.report_filename = f'{self.pig_name}_jobs_audit_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.html'
        self.yesterday_file = f'{self.pig_instance}/jobs.xml'
        self.today_file = f'{self.export_zip_name.removesuffix(".zip")}/jobs.xml'
        self.access_token = get_access_token()
        self.export_filename = f'jobs_audit_{datetime.now().strftime("%Y%m%d")}'
        self.url = f'https://{self.instance_string}/on/demandware.servlet/webdav/Sites/Impex/src/instance/{self.export_zip_name}'

    def trigger_sfcc_site_import_archive_job(self):
        payload = {
            "data_units": {
                "global_data": {
                    "job_schedules": True
                }
            },
            "export_file": self.export_filename,
            "overwrite_export_file": True
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.access_token
        }

        try:
            with httpx.Client() as client:
                run_job_response = client.post(self.job_trigger_url, headers=headers, json=payload)
                run_job_response.raise_for_status()
                return run_job_response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error(f'POST request failed with status code: {e.response.status_code}')
        except Exception as e:
            self.logger.error(f'An error occurred: {str(e)}')
        return None

    def download_file(self):
        try:
            with httpx.Client(auth=(self.business_email, self.sfcc_pass)) as client:
                download_file_response = client.get(self.url)
                download_file_response.raise_for_status()

                file_name = self.url.split("/")[-1]
                with open(file_name, "wb") as file:
                    file.write(download_file_response.content)

                self.logger.info(f'{file_name} downloaded successfully.')
                return file_name  # Return the downloaded file's name
        except httpx.HTTPStatusError as e:
            self.logger.error(f'Failed to download the file with status code: {e.response.status_code}')
        except Exception as e:
            self.logger.error(f'An error occurred while downloading the file: {str(e)}')
        return None

    def remove_remote_file(self):
        remote_file_url = f'https://{self.instance_string}/on/demandware.servlet/webdav/Sites/Impex/src/instance/{self.export_zip_name}'

        try:
            with httpx.Client(auth=(self.business_email, self.sfcc_pass)) as client:
                delete_file_response = client.delete(remote_file_url)
                delete_file_response.raise_for_status()

                self.logger.info(f'Successfully deleted remote file {self.export_zip_name}')
        except httpx.HTTPStatusError as e:
            self.logger.error(f'Failed to delete remote file with status code: {e.response.status_code}')
        except Exception as e:
            self.logger.error(f'An error occurred while deleting the remote file: {str(e)}')

    def unzip_file(self):
        try:
            with zipfile.ZipFile(self.export_zip_name, 'r') as zip_ref:
                zip_ref.extractall()
            self.logger.info(f'Successfully unzipped {self.export_zip_name}')
        except zipfile.BadZipFile:
            self.logger.error(f'Error: {self.export_zip_name} is not a valid ZIP file')
        except FileNotFoundError:
            self.logger.error(f'Error: {self.export_zip_name} not found')

    def remove_local_file(self):
        try:
            os.remove(self.export_zip_name)
            self.logger.info(f'Successfully removed {self.export_zip_name}')
        except FileNotFoundError:
            self.logger.error(f'Error: {self.export_zip_name} not found')
        except PermissionError:
            self.logger.error(f'Error: Permission denied to remove {self.export_zip_name}')

    def files_are_identical(self):
        return filecmp.cmp(self.yesterday_file, self.today_file)

    def generate_difference_report(self):
        try:
            with open(self.yesterday_file, encoding='utf-8') as old_file, open(self.today_file,
                                                                               encoding='utf-8') as new_file:
                old_file_lines = old_file.readlines()
                new_file_lines = new_file.readlines()

            difference = difflib.HtmlDiff().make_file(old_file_lines, new_file_lines, self.yesterday_file,
                                                      self.today_file)

            with open(self.report_filename, 'w', encoding='utf-8') as difference_report:
                difference_report.write(difference)

        except FileNotFoundError as e:
            self.logger.error(f'Error: {e.filename} not found')
        except Exception as e:
            self.logger.error(f'An error occurred while generating the difference report: {str(e)}')

    @staticmethod
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

    def run(self):
        response = self.trigger_sfcc_site_import_archive_job()

        if response:
            self.logger.info(f'Response: {response}')

        time.sleep(10)

        downloaded_file = self.download_file()

        if downloaded_file:
            self.remove_remote_file()

        self.unzip_file()
        self.remove_local_file()

        if self.files_are_identical():
            self.logger.info('The files are identical.')
            data_for_columns = [
                ('PIG Instance', self.bm),
                ('Difference', 'NO')
            ]

            html_table = self.generate_html_table(data_for_columns)

            send_email(
                email_recipient='konstantin.yanev@merkle.com',
                email_subject='SFCC jobs difference audit',
                email_message='Hi Team, this is the jobs audit report for today.\n'
                              'It compares sfcc jobs structure and content between\n'
                              'today and yesterday on all major Primary Instance Groups.\n',
                html_table=html_table
            )

        else:
            self.logger.info('There is a difference between the files.')
            self.generate_difference_report()

            data_for_columns = [
                ('PIG Instance', self.bm),
                ('Difference', 'YES')
            ]

            html_table = self.generate_html_table(data_for_columns)

            send_email(
                email_recipient='konstantin.yanev@merkle.com',
                email_subject='SFCC jobs difference audit',
                email_message='Hi Team, this is the jobs audit report for today.\n'
                              'It compares sfcc jobs structure and content between\n'
                              'today and yesterday on all major Primary Instance Groups.\n'
                              'Differences between jobs can be found in the attachments.'
                              'With any difference in jobs proceed as per wiki scenarios.',
                html_table=html_table,
                attachment_location=str(Path.cwd() / self.report_filename)
            )


def main():
    sfcc_job_exporter = SFCCJobExporter()
    sfcc_job_exporter.run()


if __name__ == "__main__":
    main()
