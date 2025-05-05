# Use official Python image
FROM python:3.12.3

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY newsbot.py .

# Environment variables (can be overridden at runtime)
ENV REDDIT_USER_AGENT='Newsbot/1.0 by YourUsername'

# Run the application
CMD ["python", "newsbot.py"]