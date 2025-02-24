# Use the official Python image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the project files
COPY . .

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the app
CMD ["python3", "main.py"]
