# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory to /app
WORKDIR /app

# Install development tools and libraries
RUN apt-get update && \
    apt-get install -y build-essential pkg-config

# Install libmysqlclient-dev or libmariadb-dev-compat based on availability
RUN apt-get install -y libmariadb-dev-compat || apt-get install -y libmysqlclient-dev

# Copy the Streamlit app code into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose internal port 8501
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "--server.port", "8501", "jira_frt_api.py"]
