# Start with the official Python base image
FROM python:3.10

# Set the working directory to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define the command to run your app using CMD which defines your runtime
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]