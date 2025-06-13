from fastapi import FastAPI, HTTPException
from elasticsearch_client import es
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz

# Load environment variables from .env file
load_dotenv()

app = FastAPI()
default_index = os.getenv("ELASTICSEARCH_DEFAULT_INDEX", "news_2025.04")
JAKARTA_TZ = pytz.timezone('Asia/Jakarta')


@app.get("/search/news-details/")
async def search_news_details(index_name: str = default_index):
    try:
        # Gunakan body query sesuai struktur yang diinginkan
        body = {
            "size": 1,
            "_source": [
                "title",
                "author",
                "created",
                "fulltext",
                "jenis",
                "link",
                "media_url",
                "published"
            ],
            "sort": [
                {
                    "created": {
                        "order": "desc"
                    }
                }
            ]
        }
        
        response = await es.search(
            index=index_name,
            body=body
        )
        
        # Return dokumen pertama yang ditemukan
        if response["hits"]["hits"]:
            return response["hits"]["hits"][0]["_source"]
        return {"message": "No documents found"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/search/sentiment-analysis/")
async def search_sentiment_analysis(index_name: str = default_index):
    try:
        body = {
            "size": 0,  # Tidak mengambil dokumen individual
            "aggs": {
                "total_sentiment": {
                    "terms": {
                        "field": "sentiment.keyword",
                        "size": 10  # Jumlah kategori sentimen yang diambil
                    }
                },
                "total_sentiment_polisi": {
                    "terms": {
                        "field": "sentiment_polisi.keyword",
                        "size": 10
                    }
                }
            }
        }
        
        response = await es.search(
            index=index_name,
            body=body
        )
        
        # Format hasil agregasi
        sentiment_results = {}
        sentiment_polisi_results = {}
        
        # Proses hasil agregasi untuk sentiment umum
        for bucket in response["aggregations"]["total_sentiment"]["buckets"]:
            sentiment_results[bucket["key"]] = bucket["doc_count"]
        
        # Proses hasil agregasi untuk sentiment polisi
        for bucket in response["aggregations"]["total_sentiment_polisi"]["buckets"]:
            sentiment_polisi_results[bucket["key"]] = bucket["doc_count"]
        
        return {
            "total_documents": response["hits"]["total"]["value"],
            "sentiment_totals": sentiment_results,
            "sentiment_polisi_totals": sentiment_polisi_results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/search/timeline/")
async def latest_dual_sentiment_by_hour(
    index_name: str = default_index
):
    try:
        # 1. Cari tanggal terbaru di indeks
        latest_date_query = {
            "size": 0,
            "aggs": {
                "latest_date": {
                    "max": {"field": "created"}
                }
            }
        }
        
        date_response = await es.search(index=index_name, body=latest_date_query)
        latest_timestamp = date_response["aggregations"]["latest_date"]["value"]
        
        if not latest_timestamp:
            return {"message": "No documents found in index"}
        
        # 2. Konversi ke datetime object (UTC)
        latest_dt = datetime.utcfromtimestamp(latest_timestamp / 1000).replace(tzinfo=pytz.utc)
        
        # 3. Konversi ke timezone Asia/Jakarta (UTC+7)
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        latest_dt = latest_dt.astimezone(jakarta_tz)
        
        # 4. Pastikan bulan April (4)
        if latest_dt.month != 4:
            return {"message": "Latest document is not in April"}
        
        # 5. Hitung rentang waktu untuk hari terbaru
        start_of_day = latest_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # 6. Format tanggal untuk Elasticsearch
        es_date_format = "strict_date_optional_time"
        
        # 7. Query aggregasi per jam
        body = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "created": {
                                    "gte": start_of_day.isoformat(),
                                    "lte": end_of_day.isoformat(),
                                    "format": es_date_format,
                                    "time_zone": "Asia/Jakarta"
                                }
                            }
                        }
                    ]
                }
            },
            "aggs": {
                "sentiment_by_hour": {
                    "date_histogram": {
                        "field": "created",
                        "calendar_interval": "hour",
                        "format": "yyyy-MM-dd'T'HH:mm:ssxxx",  # Format yang sesuai dengan data
                        "min_doc_count": 0,
                        "time_zone": "Asia/Jakarta",
                        "extended_bounds": {
                            "min": start_of_day.isoformat(),
                            "max": end_of_day.isoformat()
                        }
                    },
                    "aggs": {
                        "public_sentiment": {
                            "terms": {
                                "field": "sentiment.keyword",
                                "size": 10
                            }
                        },
                        "police_sentiment": {
                            "terms": {
                                "field": "sentiment_polisi.keyword",
                                "size": 10
                            }
                        }
                    }
                }
            }
        }
        
        response = await es.search(index=index_name, body=body)
        
        # 8. Format hasil aggregasi
        buckets = response["aggregations"]["sentiment_by_hour"]["buckets"]
        result = []
        
        for bucket in buckets:
            time_str = bucket["key_as_string"]
            
            # Konversi ke format jam saja
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            local_time = dt.astimezone(jakarta_tz)
            hour_str = local_time.strftime("%H:%M")
            
            doc_count = bucket["doc_count"]
            
            # Format public sentiment
            public_sentiment = {}
            for term in bucket["public_sentiment"]["buckets"]:
                public_sentiment[term["key"]] = term["doc_count"]
            
            # Format police sentiment
            police_sentiment = {}
            for term in bucket["police_sentiment"]["buckets"]:
                police_sentiment[term["key"]] = term["doc_count"]
            
            result.append({
                "hour": hour_str,
                "total_documents": doc_count,
                "public_sentiment": public_sentiment,
                "police_sentiment": police_sentiment
            })
        
        return {
            "date": start_of_day.strftime("%Y-%m-%d"),
            "timezone": "Asia/Jakarta",
            "hourly_data": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/latest-dual-sentiment-by-hour/")
async def latest_dual_sentiment_by_hour(
    index_name: str = default_index
):
    try:
        # 1. Cari tanggal terbaru di indeks dengan query yang lebih efisien
        date_query = {
            "size": 1,
            "sort": [{"created": {"order": "desc"}}],
            "_source": ["created"]
        }
        
        date_response = await es.search(index=index_name, body=date_query)
        
        if not date_response["hits"]["hits"]:
            return {"message": "No documents found in index"}
        
        # 2. Ekstrak tanggal terbaru langsung dari dokumen
        latest_dt_str = date_response["hits"]["hits"][0]["_source"]["created"]
        latest_dt = datetime.fromisoformat(latest_dt_str).astimezone(JAKARTA_TZ)
        
        # 3. Validasi bulan April
        if latest_dt.month != 4:
            return {"message": "Latest document is not in April"}
        
        # 4. Hitung rentang waktu untuk hari terbaru
        start_of_day = latest_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # 5. Format tanggal untuk Elasticsearch
        es_date_format = "strict_date_optional_time"
        
        # 6. Query aggregasi per jam yang dioptimalkan
        body = {
            "size": 0,
            "query": {
                "range": {
                    "created": {
                        "gte": start_of_day.isoformat(),
                        "lte": end_of_day.isoformat(),
                        "format": es_date_format,
                        "time_zone": "Asia/Jakarta"
                    }
                }
            },
            "aggs": {
                "sentiment_by_hour": {
                    "date_histogram": {
                        "field": "created",
                        "fixed_interval": "1h",  # Menggunakan fixed interval
                        "min_doc_count": 0,
                        "time_zone": "Asia/Jakarta",
                        "extended_bounds": {
                            "min": start_of_day.isoformat(),
                            "max": end_of_day.isoformat()
                        }
                    },
                    "aggs": {
                        "public_sentiment": {
                            "terms": {
                                "field": "sentiment.keyword",
                                "size": 3  # Hanya ambil 3 kategori utama
                            }
                        },
                        "police_sentiment": {
                            "terms": {
                                "field": "sentiment_polisi.keyword",
                                "size": 3
                            }
                        },
                        "doc_count_bucket": {
                            "bucket_script": {
                                "buckets_path": {},
                                "script": "params._value0"
                            }
                        }
                    }
                }
            }
        }
        
        # 7. Eksekusi query
        response = await es.search(index=index_name, body=body)
        
        # 8. Proses hasil yang lebih efisien
        buckets = response["aggregations"]["sentiment_by_hour"]["buckets"]
        result = []
        
        for bucket in buckets:
            # Format waktu langsung dari key (timestamp)
            hour_dt = datetime.fromtimestamp(bucket["key"] / 1000, tz=JAKARTA_TZ)
            hour_str = hour_dt.strftime("%H:%M")
            
            # Format sentimen dengan default 0 untuk kategori yang tidak ada
            public_sentiment = {term["key"]: term["doc_count"] 
                               for term in bucket["public_sentiment"]["buckets"]}
            
            police_sentiment = {term["key"]: term["doc_count"] 
                               for term in bucket["police_sentiment"]["buckets"]}
            
            result.append({
                "hour": hour_str,
                "total_documents": bucket["doc_count"],
                "public_sentiment": public_sentiment,
                "police_sentiment": police_sentiment
            })
        
        return {
            "date": start_of_day.strftime("%Y-%m-%d"),
            "timezone": "Asia/Jakarta",
            "hourly_data": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))