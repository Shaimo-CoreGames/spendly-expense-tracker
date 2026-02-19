FROM python:3.11-slim

WORKDIR /app

# Install system packages required for some Python libraries
RUN apt-get update && apt-get install -y build-essential gfortran libblas-dev liblapack-dev wget && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .

# Upgrade pip and install dependencies with a longer timeout
RUN python -m pip install --upgrade pip
RUN pip install --default-timeout=300 --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start the app
CMD ["uvicorn", "main_ml:app", "--host", "0.0.0.0", "--port", "8000"]
