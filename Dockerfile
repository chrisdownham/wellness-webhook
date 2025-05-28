# Use the official Playwright image matching your pip package version
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py start.sh ./

# Install Playwright browsers
RUN playwright install

# Expose the port your Flask app will run on
EXPOSE 5000

# Launch script
CMD ["bash", "start.sh"]
