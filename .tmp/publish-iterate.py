from botocore.exceptions import NoCredentialsError
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
from flask import Flask
from prometheus_client import Counter, generate_latest, REGISTRY, Gauge
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

# Replace these with your AWS details
opensearch_index = 'ops-logs-*'
opensearch_host = "logs.testing.perception-point.io"
opensearch_port = 443
service = 'es'

session = boto3.Session()
credentials = session.get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, session.region_name, service, session_token=credentials.token)

# Create an OpenSearch instance with AWS authentication
client = OpenSearch(
    hosts=[{'host': opensearch_host, 'port': opensearch_port}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
    connection_class=RequestsHttpConnection
)

app = Flask(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests')
LAST_FETCH_TIME = Gauge('last_fetch_time', 'Timestamp of the last OpenSearch data fetch')

def fetch_data():
    start_time = datetime.utcnow() - timedelta(minutes=10)
    end_time = datetime.utcnow()

    start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    query = {
        "aggs": {
            "2": {
                "terms": {
                    "field": "str_1",
                    "order": {
                        "_key": "desc"
                    },
                    "size": 100
                },
                "aggs": {
                    "1": {
                        "percentiles": {
                            "field": "float_1",
                            "percents": [
                                50
                            ]
                        }
                    },
                    "3": {
                        "top_hits": {
                            "docvalue_fields": [
                                {
                                    "field": "scan_id"
                                }
                            ],
                            "_source": "scan_id",
                            "size": 1,
                            "sort": [
                                {
                                    "@timestamp": {
                                        "order": "desc"
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        },
        "size": 0,
        "stored_fields": ["*"],
        "script_fields": {},
        "docvalue_fields": [
            {"field": "@timestamp", "format": "date_time"},
            {"field": "log_date", "format": "date_time"}
        ],
        "_source": {"excludes": []},
        "query": {
            "bool": {
                "must": [],
                "filter": [
                    {"match_all": {}},
                    {"match_phrase": {"action": "timer"}},
                    {"match_phrase": {"sample_type": "email"}},
                    {
                        "range": {
                            "@timestamp": {
                                "gte": start_time_str,
                                "lte": end_time_str,
                                "format": "strict_date_optional_time"
                            }
                        }
                    }
                    # Add your additional filters or conditions here if needed
                ],
                "should": [],
                "must_not": []
            }
        }
    }

    result = client.search(index=opensearch_index, body=query)
    LAST_FETCH_TIME.set(int(end_time.timestamp()))  # Set the last fetch time metric

    # Additional processing or exposing of metrics can be done here

@app.route('/metrics')
def metrics():
    REQUEST_COUNT.inc()  # Increment the request count metric
    fetch_data()  # Fetch data before exposing metrics
    return generate_latest(REGISTRY)

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_data, 'interval', seconds=10)  
    scheduler.start()

    app.run(host='0.0.0.0', port=5000)
