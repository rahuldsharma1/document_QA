# Use an official lightweight Python image.
FROM python:3.9-slim

# Set the working directory.
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    libtiff-dev \
    zlib1g-dev \
    libopenjp2-7-dev \
    libpoppler-cpp-dev \
    tesseract-ocr \
    libleptonica-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies.
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN python -m nltk.downloader punkt punkt_tab

COPY .env /app/

# Copy the backend source code.
COPY . /app/

# Expose port 8000.
EXPOSE 8000

# Run the FastAPI app.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]