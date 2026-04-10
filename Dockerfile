# Use the official Python 3.10 slim image
FROM python:3.10-slim

# Create a user to avoid running as root (required by Hugging Face Spaces security guidelines)
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Install system libraries necessary for OpenCV and EasyOCR
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY --chown=user requirements.txt .

# Install dependencies (running as the new user)
USER user
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy the rest of the application code
COPY --chown=user . .

# Expose port 7860 (Hugging Face Spaces default for Docker)
EXPOSE 7860

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port", "7860", "--server.address", "0.0.0.0"]
