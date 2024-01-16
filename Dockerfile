# Use the official Python image as a base image
FROM python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY requirements.txt fetch.py /app/

# Expose the port that your Flask app will run on
EXPOSE 5000

# Run app.py when the container launches
CMD ["python", "fetch.py"]
