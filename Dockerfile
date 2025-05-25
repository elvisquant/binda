# # Use official Python image
# FROM python:3.11-slim

# # Set environment vars
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# # Set working directory
# WORKDIR /app

# # Install dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy project
# COPY . .

# # Run app
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]




# Stage 1: Build the application and install dependencies
FROM python:3.11-slim-bookworm AS builder

# Set the working directory
WORKDIR /app

# Install build essentials if any of your dependencies need to compile C extensions
# (Often needed for libraries like psycopg2, numpy, pandas, etc.)
# If you are sure you don't need them, you can comment this out.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    # Add any other system-level dependencies your Python packages might need
    # For example, for psycopg2: libpq-dev
    # For example, for Pillow: libjpeg-dev zlib1g-dev
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir: Reduces image size by not storing the pip cache
# --prefix=/install: Installs packages into a specific directory, making it easier to copy to the final stage
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Copy the rest of your application code
COPY ./app /app/app


# Stage 2: Create the final production image
FROM python:3.11-slim-bookworm AS runner

# Set the working directory
WORKDIR /app

# Create a non-root user for security best practices
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 --shell /bin/bash --create-home appuser

# Copy installed Python packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application code from the builder stage
COPY --from=builder /app/app /app/app

# Ensure the appuser owns the application files
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the port the app runs on (default for Uvicorn is 8000)
EXPOSE 8000

# Command to run the Uvicorn server
# --host 0.0.0.0 makes the server accessible from outside the container
# --port 8000 specifies the port
# app.main:app refers to the `app` instance in your `app/main.py` file
# Adjust `app.main:app` if your app instance or file structure is different
# --reload is useful for development, but remove it for production for better performance
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
