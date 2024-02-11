from elasticsearch import Elasticsearch
from requests_aws4auth import AWS4Auth
import boto3

region = "us-east-2"
opensearch_host = "logs.perception-point.io"
opensearch_port = 443
opensearch_index = 'ops-logs-*'


session = boto3.Session()
credentials = session.get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)

es = Elasticsearch(
    hosts=[{'host': opensearch_host, 'port': opensearch_port}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

query = {
    "aggs": {
        "2": {
            "terms": {
                "field": "str_1",
                "order": {"1": "desc"},
                "size": 20
            },
            "aggs": {
                "1": {"avg": {"field": "float_1"}},
                "3": {"percentiles": {"field": "float_1", "percents": [50]}},
                "4": {"max": {"field": "float_1"}}
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
                {"match_phrase": {"kubernetes.namespace": "eu"}},
                {"match_phrase": {"kubernetes.container.name": "mantis-worker-url"}},
                {"match_phrase": {"action": "timer"}},
                {
                    "range": {
                        "@timestamp": {
                            "gte": "2024-01-07T10:24:15.449Z",
                            "lte": "2024-01-07T10:39:15.449Z",
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

# Specify the index and execute the query
result = es.search(index=opensearch_index, body=query)

# Process the result (this is a basic example, you may need to adapt it to your data structure)
for hit in result['aggregations']['2']['buckets']:
    term_value = hit['key']
    avg_value = hit['1']['value']
    percentiles_50 = hit['3']['values']['50.0']
    max_value = hit['4']['value']
    
    # Process and use the aggregated data as needed
    print(f"Term: {term_value}, Avg: {avg_value}, Percentiles 50: {percentiles_50}, Max: {max_value}")