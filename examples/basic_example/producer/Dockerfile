# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /usr/src/app

# Install nodejs and npm
RUN apt-get update && apt-get install -y nodejs npm

# Install nodemon globally
RUN npm install -g nodemon

# Copy the rest of the application code
COPY . .

# Install fast_rabbit
RUN pip install fast_rabbit

# Start the application using nodemon for automatic reloading on file changes
CMD ["nodemon", "--exec", "python", "./main.py", "--watch", ".", "--ext", "py"]
