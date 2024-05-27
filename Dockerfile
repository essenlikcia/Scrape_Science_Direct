FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libjpeg-dev \
    libopenjp2-7-dev \
    zlib1g-dev \
    pkg-config \
    python3-dev \
    default-libmysqlclient-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY .env /app/
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install PyMuPDF frontend tools
COPY . /app/

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]