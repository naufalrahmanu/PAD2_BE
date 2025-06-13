from elasticsearch import AsyncElasticsearch
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

ES_HOST = os.getenv("ELASTICSEARCH_HOST")
ES_USER = os.getenv("ELASTICSEARCH_USER")
ES_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")

# Create an instance of AsyncElasticsearch
es = AsyncElasticsearch(
    hosts=[ES_HOST],
    http_auth=(ES_USER, ES_PASSWORD) if ES_USER and ES_PASSWORD else None
)