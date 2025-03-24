# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Copy the Streamlit app code into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose internal port 8502
EXPOSE 8503

# Run the Streamlit app
CMD ["streamlit", "run", "--server.enableCORS", "false", "--server.port", "8503", "app.py"]
