# PAD2_Backend

This project provides a RESTful API for analyzing sentiment data from news articles using FastAPI and Elasticsearch.

![FastApi](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Elastic_Search](https://img.shields.io/badge/Elastic_Search-005571?style=for-the-badge&logo=elasticsearch)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)

## Tech Stack

**FastAPI** 

**Elasticsearch**

**Python 3.9**

**Docker**

## Project Structure

```text
PAD2_Beckend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints.py         # Endpoint API utama
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Konfigurasi aplikasi
│   ├── elasticsearch/
│   │   ├── __init__.py
│   │   ├── client.py            # Klien Elasticsearch
│   │   ├── queries.py           # Kumpulan query ES
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sentiment_service.py # Layanan analisis sentimen
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── date_utils.py        # Utilitas tanggal/waktu
│   ├── main.py                  # Entry point aplikasi
│   ├── Dockerfile
│   └── requirements.txt         # Dependensi Python
├── .env.example                 # Template environment variables
├── docker-compose.yml           # Konfigurasi Docker Compose
├── README.md                    # Dokumentasi proyek
└── .gitignore
```

## Installation

1. Clone repositori:
```bash
git clone https://github.com/naufalrahmanu/PAD2_Backend.git
cd app
```
2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Jalankan aplikasi
```python
python -m uvicorn main:app --reload
```
## API Endpoint

#### Sentiment

```http
GET /search/sentiment-analysis
```

#### Berita terbaru

```http
GET /search/news-details
```

#### Timeline
```http
GET /search/timeline
```
