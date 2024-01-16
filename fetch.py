from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from prometheus_client import Counter, generate_latest, REGISTRY, Gauge
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
QUERY_TIME_REFRESH = int(os.getenv('QUERY_TIME_REFRESH', 60)) # seconds

global session, awsauth
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
opensearch_index = os.getenv('opensearch_index','ops-logs-*')
opensearch_host = os.getenv('opensearch_host','logs.testing.perception-point.io')
opensearch_port = int(os.getenv('opensearch_port',443))
service = 'es'
start_time = datetime.utcnow() - timedelta(minutes=QUERY_TIME_LAG+QUERY_TIME_RANGE)
end_time = datetime.utcnow() - timedelta(minutes=QUERY_TIME_LAG)
start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
labels = [
    'unpack',
    'scanning',  
    'start_remote_scan', 
    'scan_duration',
    '_static_scan_and_unpacking',
    'extract_scan',
    'extract_scan.WeTransferDownloadURLExtractor',
    'browse_and_wait_until_loaded',
    'extract_scan.GoogleSpreadsheetsDownloadURLExtractor',
    'extract_scan.HtmlDynamicEvidenceExtractor',
    'extract_scan.TwoStepExtractor',
    'extract_scan.GoogleDocsDownloadURLExtractor',
    'extract_scan.GenericSeleniumCrawlerExtractor',  
    '_create_chrome_driver',
    'run_decisions',
    'scanner.URLScreenshotScanner',
    'extract_scan.GoogleDriveDownloadURLExtractor',
    'extract_scan.URLScreenshotExtractor',
    'extract_scan.SharepointDownloadExtractor',
    'extract_scan.FaviconExtractor'
]
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
                # Add your additional filters or conditions here if needed
            ],
            "should": [],
            "must_not": []
        }
    }
}
app = Flask(__name__)

def refresh_aws_credentials():
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, session.region_name, service, session_token=credentials.token)
        client = OpenSearch(
            hosts=[{'host': opensearch_host, 'port': opensearch_port}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
            connection_class=RequestsHttpConnection
        )
        # result = client.search(index=opensearch_index, body=query)
        logger.info("AWS credentials refreshed successfully.")
    
    except (NoCredentialsError, PartialCredentialsError) as e:
        logger.error(f"Error refreshing AWS credentials: {e}")

def fetch_data():
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, session.region_name, service, session_token=credentials.token)
        client = OpenSearch(
            hosts=[{'host': opensearch_host, 'port': opensearch_port}],
            use_ssl=True,
            http_auth=awsauth,
            verify_certs=True,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
            connection_class=RequestsHttpConnection
        )
        print(query)
        result = client.search(index=opensearch_index, body=query)
        print(result)
        buckets = result['aggregations']['2']['buckets']
        for bucket in buckets:
            function_label_key = bucket['key']
            if function_label_key in labels:
            #     # Average
                average_float_1_value = bucket['1']['value']
                AVERAGE_FLOAT_1_GAUGE.labels(function=function_label_key).set(average_float_1_value)
                # print(f"Function: {function_label_key}, Average float_1: {average_float_1_value}")
            #     # Median
                median_float_1_value = bucket['3']['values']['50.0']
                MEDIAN_FLOAT_1_GAUGE.labels(function=function_label_key).set(median_float_1_value)
                # print(f"Function: {function_label_key}, Median float_1: {median_float_1_value}")
            #     # Max
                max_float_1_value = bucket['4']['value']
                MAX_FLOAT_1_GAUGE.labels(function=function_label_key).set(max_float_1_value)
                # print(f"Function: {function_label_key}, Max float_1: {max_float_1_value}")
            #    # Count
                function_count = bucket['doc_count']
                FUNCTION_COUNT_GUAGE.labels(function=function_label_key).set(function_count)
                # print(f"Function: {function_label_key}, Count: {function_count}")
        LAST_FETCH_TIME.set(int(end_time.timestamp()))

    except NoCredentialsError:
        logger.warning("AWS credentials need refreshing.")
        refresh_aws_credentials()
        raise

    except AuthorizationException as e:
        logger.error(f"Error: Invalid security token - {e}")
        refresh_aws_credentials()
        raise

    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        raise

# Register the error handler
@app.errorhandler(Exception)
def handle_error(error):
    return jsonify({'error': str(error)}), 500

@app.route('/metrics')
def metrics():
    REQUEST_COUNT.inc()  
    fetch_data() 
    if hasattr(g, 'exception'):
        return g.exception, 500  
    else:
        return generate_latest(REGISTRY)

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_data, 'interval', seconds=QUERY_TIME_REFRESH) 
    scheduler.start()
    app.run(host='0.0.0.0', port=5000)