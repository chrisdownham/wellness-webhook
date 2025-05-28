# 1. Use Playwright’s official Python image (includes all browser deps)
FROM mcr.microsoft.com/playwright/python:latest

# 2. Set working directory
WORKDIR /app

# 3. Copy in your app + deps files
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of your code
COPY app.py start.sh railway.json ./

# 5. Install browsers (already baked into the base image, but safe)
RUN playwright install

# 6. Expose port (Railway uses $PORT env variable at runtime)
EXPOSE 5000

# 7. Start your app
CMD ["bash", "start.sh"]
