# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy container code
COPY . .

# Copy the local module and the requirements file first
# COPY /utils/ /utils/
# COPY requirements.txt requirements.txt

# Install dependencies, including the local module in "editable" mode
RUN pip install -r requirements.txt

# Expose the port the app runs on
EXPOSE 5055

# Run the application
CMD ["python", "app.py"]
