JiraData Class
--------------

The `JiraData` class is responsible for retrieving JIRA data from a MySQL database using the `MySQLdb` library and processing it with `pandas`.

Attributes:

- `host`: MySQL database host
- `user`: MySQL database user
- `password`: MySQL database password
- `database`: JIRA database name
- `db`: MySQL database connection object

Methods:

- `connect()`: Establishes a connection to the MySQL database.
- `close_connection()`: Closes the connection to the MySQL database.
- `get_first_response_time(project_number, days_interval)`: Retrieves First Response Time (FRT) data from the JIRA database.

ExcelExporter Class
-------------------

The `ExcelExporter` class facilitates exporting a `pandas` DataFrame to an Excel file.

Attributes:

- `filename`: Name of the Excel file to be created.

Methods:

- `export_to_excel(dataframe)`: Exports a DataFrame to an Excel file.

StreamlitApp Class
------------------

The `StreamlitApp` class represents the Streamlit application for user interaction and displaying results.

Attributes:

- `host`, `user`, `password`, `database`: JIRA database configurations
- `project_number`, `days_interval`: User inputs
- `first_response_time`: Instance of `JiraData` for data retrieval
- `excel_exporter`: Instance of `ExcelExporter` for exporting data

Methods:

- `run()`: Runs the Streamlit application.
- `display_download_button()`: Displays the download button for the exported Excel file.
