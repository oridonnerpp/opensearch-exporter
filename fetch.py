from prometheus_client import gc_collector, platform_collector, process_collector
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from prometheus_client import Counter, generate_latest, REGISTRY, Gauge, CollectorRegistry
from apscheduler.schedulers.background import BackgroundScheduler
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import AuthorizationException
from datetime import datetime, timedelta
from requests_aws4auth import AWS4Auth
from flask import Flask, jsonify, g

import boto3
import logging
import sys
import os

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests')
LAST_FETCH_TIME = Gauge('last_fetch_time', 'Timestamp of the last OpenSearch data fetch')
AVERAGE_FLOAT_1_GAUGE = Gauge('Average_float_1','Average float_1 value for scanning and start_remote_scan',['function'])
MEDIAN_FLOAT_1_GAUGE = Gauge('Median_float_1', 'Median_float_1 gauge', ['function'])
MAX_FLOAT_1_GAUGE = Gauge('Max_float_1', 'Max_float_1 gauge', ['function'])
FUNCTION_COUNT_GUAGE = Gauge('function_count', 'Total number of function calls', ['function'])
QUERY_TIME_RANGE = int(os.getenv('QUERY_TIME_RANGE', 60)) # minutes
QUERY_TIME_LAG = int(os.getenv('QUERY_TIME_LAG', 30)) # minutes
QUERY_TIME_REFRESH = int(os.getenv('QUERY_TIME_REFRESH', 10)) # seconds

# App Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenSearch Client
global awsauth, session, credentials, client, query, opensearch_index, opensearch_host, opensearch_port, start_time, end_time
opensearch_index = os.getenv('opensearch_index','ops-logs-*')
opensearch_host = os.getenv('opensearch_host','logs.perception-point.io')
opensearch_port = int(os.getenv('opensearch_port',443))
start_time = datetime.utcnow() - timedelta(minutes=QUERY_TIME_LAG+QUERY_TIME_RANGE)
end_time = datetime.utcnow() - timedelta(minutes=QUERY_TIME_LAG)
start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
query = {
    "aggs": {
        "2": {
        "terms": {
            "field": "str_1",
            "order": {
            "_key": "desc"
            },
            "size": 1000
        },
        "aggs": {
            "1": {
            "avg": {
                "field": "float_1"
            }
            },
            "3": {
            "percentiles": {
                "field": "float_1",
                "percents": [
                50
                ]
            }
            },
            "4": {
            "max": {
                "field": "float_1"
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
            ],
            "should": [],
            "must_not": []
        }
    }
}


# Flask
app = Flask(__name__)

def fetch_data():
    session = boto3.Session()
    credentials = session.get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, session.region_name, 'es', session_token=credentials.token)
    print(f"============================== Refreshed Access Key: {credentials.access_key} ================================")        
    client = OpenSearch(
        hosts=[{'host': opensearch_host, 'port': opensearch_port}],
        use_ssl=True,
        http_auth=awsauth,
        verify_certs=True,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        connection_class=RequestsHttpConnection
    )
    start_time = datetime.utcnow() - timedelta(minutes=QUERY_TIME_LAG+QUERY_TIME_RANGE)
    end_time = datetime.utcnow() - timedelta(minutes=QUERY_TIME_LAG)
    start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    time_now = datetime.utcnow()
    query = {
    "aggs": {
        "2": {
        "terms": {
            "field": "str_1",
            "order": {
            "_key": "desc"
            },
            "size": 1000
        },
        "aggs": {
            "1": {
            "avg": {
                "field": "float_1"
            }
            },
            "3": {
            "percentiles": {
                "field": "float_1",
                "percents": [
                50
                ]
            }
            },
            "4": {
            "max": {
                "field": "float_1"
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
            ],
            "should": [],
            "must_not": []
        }
    }
}
    print(f"============================== Now: {time_now} ============================")
    print(f"============================== Start Time Str: {start_time_str} ================================")
    print(f"============================== End Time Str: {end_time_str} ================================")
    print(f"============================== Query: {query} ================================")

    custom_metrics = []
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        if isinstance(collector, Gauge):  
            custom_metrics.append(collector)

    result = client.search(index=opensearch_index, body=query)
    buckets = result['aggregations']['2']['buckets']
    for bucket in buckets:
        function_label_key = bucket['key']
        average_float_1_value = bucket['1']['value']
        AVERAGE_FLOAT_1_GAUGE.labels(function=function_label_key).set(average_float_1_value)
        median_float_1_value = bucket['3']['values']['50.0']
        MEDIAN_FLOAT_1_GAUGE.labels(function=function_label_key).set(median_float_1_value)
        max_float_1_value = bucket['4']['value']
        MAX_FLOAT_1_GAUGE.labels(function=function_label_key).set(max_float_1_value)
        function_count = bucket['doc_count']
        FUNCTION_COUNT_GUAGE.labels(function=function_label_key).set(function_count)
    LAST_FETCH_TIME.set(int(end_time.timestamp()))
    
    # Unregister custom collectors.
    for collector in collectors:
        REGISTRY.unregister(collector)

    # Re-register default collectors.
    process_collector.ProcessCollector()
    platform_collector.PlatformCollector()
    gc_collector.GCCollector()

    # Re-register custom collectors
    for metric in custom_metrics:
        REGISTRY.register(metric)





# Register the error handler
@app.errorhandler(Exception)
def handle_error(error):
    return jsonify({'error': str(error)}), 500

@app.route('/metrics')
def metrics():
    REQUEST_COUNT.inc()
    if hasattr(g, 'exception'):
        return g.exception, 500
    else:
        return generate_latest(REGISTRY)

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_data, 'interval', seconds=QUERY_TIME_REFRESH)
    scheduler.start()
    app.run(host='0.0.0.0', port=5000)