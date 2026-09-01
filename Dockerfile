# Use the official Microsoft Playwright image
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install Python dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script, the .pkl models, and the .csv database
COPY . .

# The command Render will run every morning
CMD ["python", "main.py"]