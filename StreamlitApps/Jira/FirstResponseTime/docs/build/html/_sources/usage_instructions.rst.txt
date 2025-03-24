============
Usage Guide
============

Standalone Script
------------------

To use this app as a standalone script, follow these steps:

1. Refactoring:
   - Some refactoring is required to adapt the app to your needs. Refer to the documentation for guidance.

2. Install Dependencies:
   - Review the ``requirements.txt`` file and install the necessary dependencies using:
     ::
     
       pip install -r requirements.txt

3. Configuration:
   - Populate the ``.env`` file with the required data before executing the script.
   - Ensure you are logged in to the VPN, specifically for our Corporate Jira DB.

4. Assistance:
   - If you encounter difficulties, feel free to message us on Slack for assistance.

5. Identify Us:
   - Get to know more about the contributors by referring to the documentation.

Docker Deployment
------------------

To deploy this app using Docker, follow these steps:

1. Install Docker Engine:
   - Follow the installation guide for your operating system: https://docs.docker.com/engine/install/

2. Install Docker Compose:
   - Refer to the official guide for standalone installation: https://docs.docker.com/compose/install/standalone/

3. Docker Files:
   - The necessary files, including ``get_first_response_time.py``, ``Dockerfile``, ``requirements.txt``, and ``docker-compose.yml``, are finalized and require no additional work.

4. Configuration:
   - Populate the ``.env`` file with the required data.

5. Exposed Port:
   - The internal port 8501 of the Docker container will be exposed and mapped to port 8501 on the host.
   - Ensure that port 8501 is available on the host. This is the standard port for Streamlit applications, but you can substitute it with an available port in the range 8501-8599.

6. Build the Docker Image:
   - Run the following command to build the Docker image:
     ::
     
       docker-compose build

7. Run the Docker Container:
   - Start an instance of the Docker image as a container:
     ::
     
       docker-compose up -d

8. Access the App:
- Ensure you are logged in to the VPN, specifically for our Corporate Jira DB.
   - Open the app in your browser:
     - If running on your local machine, go to http://localhost:8501/
     - If on another host, replace "localhost" with the appropriate hostname.

Using the Streamlit Web Interface
----------------------------------

1. Input Data:
   - Enter the JIRA project number and desired days interval.

2. Retrieve Data:
   - Click the "Get First Response Time" button to fetch and export data.

3. Download Data:
   - Use the provided button to download the exported Excel file.
