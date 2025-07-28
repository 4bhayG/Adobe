# Use an official lightweight Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script into the container at /app
COPY app.py .

# Create mount points for input and output
# Although volumes are mounted at runtime, this is good practice
RUN mkdir -p /app/input /app/output

# Set the command to run when the container launches
CMD ["python", "app.py"]