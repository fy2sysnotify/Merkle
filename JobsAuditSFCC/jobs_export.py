from datetime import datetime
from typing import Optional, Dict, Any
import httpx
from decouple import config
from client_creds_token import get_access_token


class SFCCSiteImportJobTrigger:
    def __init__(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> None:
        self.url = url
        self.headers = headers
        self.payload = payload

    def trigger_job(self) -> Optional[Dict[str, Any]]:
        """
        Triggers a site import export job in Salesforce Commerce Cloud site.

        :return: Response JSON if successful, None otherwise.
        """
        access_token = get_access_token()
        self.headers['Authorization'] = 'Bearer ' + access_token

        try:
            with httpx.Client() as client:
                client.headers.update(self.headers)
                response = client.post(self.url, json=self.payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            print(f'POST request to {self.url} failed with status code: {e.response.status_code}')
        except Exception as e:
            print(f'An error occurred while making POST request to {self.url}: {str(e)}')
        return None


def main():
    job_trigger_url = f'https://{config("FQDN", default="")}/s/-/dw/data/v21_10/jobs/sfcc-site-archive-export/executions'
    export_filename = f'global_data_jobs_export_programmatic_{datetime.now().strftime("%Y%m%d")}'

    headers = {
        'Content-Type': 'application/json',
    }

    payload = {
        "data_units": {
            "global_data": {
                "job_schedules": True
            }
        },
        "export_file": export_filename,
        "overwrite_export_file": True
    }

    job_trigger: SFCCSiteImportJobTrigger = SFCCSiteImportJobTrigger(url=job_trigger_url, headers=headers,
                                                                     payload=payload)
    job_response = job_trigger.trigger_job()

    if job_response:
        print("Response:", job_response)
        job_id = job_response['id']
        print(job_id)


if __name__ == "__main__":
    main()
