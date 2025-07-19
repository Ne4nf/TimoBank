FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app

# Create startup script that runs data generation then starts server
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🏦 Starting TIMO Banking Platform..."\n\
echo "📊 Initializing database with sample data..."\n\
cd /app/src\n\
python generate_data.py --customers 30 --transactions 150 --auth-logs 100\n\
echo "✅ Database initialization completed!"\n\
echo "🚀 Starting FastAPI server..."\n\
cd /app/backend\n\
uvicorn main:app --host 0.0.0.0 --port $PORT' > /app/start.sh && chmod +x /app/start.sh

# Expose port (Render will set $PORT automatically)
EXPOSE $PORT

# Run startup script
CMD ["/app/start.sh"]
