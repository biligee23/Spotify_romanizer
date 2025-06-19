# Use an official Python runtime as a parent image
# Change this line to reflect Python 3.11
FROM --platform=linux/amd64 python:3.11-slim

# Set the working directory in the container
WORKDIR /app
# Copy the requirements file first to leverage Docker cache
# This ensures that if only your code changes, the pip install step isn't re-run.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
# The dot '.' refers to the build context (your project root directory)
COPY . .

# IMPORTANT: Adjust PYTHONPATH to include 'src'
# This tells Python to look inside the 'src' folder for modules.
ENV PYTHONPATH="${PYTHONPATH}:/app/src"
ENV PYTHONUNBUFFERED=1

# Optional: Use a non-root user
RUN useradd -m appuser
USER appuser

# Make port 5000 available to the world outside this container
# This is documentation; it doesn't actually publish the port.
EXPOSE 5000

# Command to run the application
# For development:
CMD ["python", "src/app.py"]
# For production:
# CMD ["gunicorn", "-b", "0.0.0.0:5000", "src.app:create_app()"]
