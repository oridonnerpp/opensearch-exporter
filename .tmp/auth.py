from botocore.exceptions import NoCredentialsError
from opensearchpy import OpenSearch, RequestsHttpConnection
# from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3

# Replace these with your AWS details
opensearch_index = 'ops-logs-*'
opensearch_host = "logs.testing.perception-point.io"
opensearch_port = 443 
service = 'es'



session = boto3.Session()
credentials = session.get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, session.region_name, service, session_token=credentials.token)


# Create an opensearch instance with AWS authentication
client = OpenSearch(
    hosts=[{'host': opensearch_host, 'port': opensearch_port}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    ssl_assert_hostname = False,
    ssl_show_warn = False,
    connection_class=RequestsHttpConnection
)
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
              "gte": "2024-01-07T15:09:32.349Z",
              "lte": "2024-01-07T15:24:32.349Z",
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
  
print(result)


# for hit in result['aggregations']['2']['buckets']:
#     term_value = hit['key']
#     avg_value = hit['1']['values']['50.0']  # Using 'values' for percentiles aggregation
#     top_hit = hit['3']['hits']['hits'][0]
#     max_value = top_hit['_source']['scan_id']  
#     # Process and use the aggregated data as needed
#     print(f"Term: {term_value}, Avg: {avg_value}, Percentiles 50: {top_hit}, Max: {max_value}")
