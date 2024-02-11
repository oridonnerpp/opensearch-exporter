from botocore.exceptions import NoCredentialsError
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import time
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

def fetch_data():

    # start_time = "2024-01-07T15:09:32.349Z"
    # end_time = "2024-01-07T15:24:32.349Z"
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(seconds=10)
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
        "stored_fields": [
            "*"
        ],
        "script_fields": {},
        "docvalue_fields": [
            {
                "field": "@timestamp",
                "format": "date_time"
            },
            {
                "field": "log_date",
                "format": "date_time"
            }
        ],
        "_source": {
            "excludes": []
        },
        "query": {
            "bool": {
                "must": [],
                "filter": [
                    {
                        "match_all": {}
                    },
                    {
                        "match_phrase": {
                            "action": "timer"
                        }
                    },
                    {
                        "match_phrase": {
                            "sample_type": "email"
                        }
                    },
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
    # Specify the index and execute the query
    result = client.search(index=opensearch_index, body=query)
    # Print the entire result for now
    print(f"Result: {result}")
    print (f"start_time: {start_time_str}")


# Infinite loop to keep the script running
i = 0
while True:
    i = i + 1
    fetch_data()
    print (f"iteration number:{i}")
    time.sleep(10)
