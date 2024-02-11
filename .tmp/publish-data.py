from flask import Flask, Response
from requests_aws4auth import AWS4Auth
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
import boto3
import requests
import schedule
import time
import threading
from botocore.exceptions import NoCredentialsError


app = Flask(__name__)

opensearch_host = "logs.testing.perception-point.io"
opensearch_port = 443
opensearch_region = "us-east-2"
opensearch_index = "ops-logs-*"
service = "es"

# Use boto3 to get OpenSearch credentials from your AWS session
session = boto3.Session()
credentials = session.get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    session.region_name,
    service,
    session_token=credentials.token,
)

# Example query
# query = {
#     "aggs": {
#         "2": {
#             "terms": {
#                 "field": "str_1",
#                 "order": {"1": "desc"},
#                 "size": 20,
#             },
#             "aggs": {
#                 "1": {"avg": {"field": "float_1"}},
#                 "3": {"percentiles": {"field": "float_1", "percents": [50]}},
#                 "4": {"max": {"field": "float_1"}},
#             },
#         }
#     },
#     "size": 0,
#     "stored_fields": ["*"],
#     "script_fields": {},
#     "docvalue_fields": [
#         {"field": "@timestamp", "format": "date_time"},
#         {"field": "log_date", "format": "date_time"},
#     ],
#     "_source": {"excludes": []},
#     "query": {
#         "bool": {
#             "must": [],
#             "filter": [
#                 {"match_all": {}},
#                 {"match_phrase": {"kubernetes.namespace": "eu"}},
#                 {"match_phrase": {"kubernetes.container.name": "mantis-worker-url"}},
#                 {"match_phrase": {"action": "timer"}},
#                 {
#                     "range": {
#                         "@timestamp": {
#                             "gte": "2024-01-07T10:24:15.449Z",
#                             "lte": "2024-01-07T10:39:15.449Z",
#                             "format": "strict_date_optional_time",
#                         }
#                     }
#                 },
#             ],
#             "should": [],
#             "must_not": [],
#         }
#     },
# }
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
      ],
      "should": [],
      "must_not": []
    }
  }
}

url = f"https://{opensearch_host}:{opensearch_port}/{opensearch_index}/_search"
headers = {"Content-Type": "application/json"}

# Use the credentials obtained from boto3 for authentication
def execute_opensearch_query():
    response = requests.post(url, json=query, headers=headers, auth=awsauth)
    # print("OpenSearch Response:", response.json())
    return response.json()



# Assuming your metrics are float values, adjust this accordingly
avg_metric = Gauge("average_metric", "Description of gauge", ["term"])

def update_metrics():
    try:
        result = execute_opensearch_query()

        if "aggregations" in result and "2" in result["aggregations"] and "buckets" in result["aggregations"]["2"]:
            avg_metric._metrics.clear()  # Clear existing metrics

            for hit in result["aggregations"]["2"]["buckets"]:
                term_value = hit["key"]
                avg_value = hit["1"]["value"]
                percentiles_50 = hit["3"]["values"]["50.0"]
                max_value = hit["4"]["value"]

                # Set the gauge metric values
                avg_metric.labels(term=term_value).set(avg_value)

    except NoCredentialsError:
        # Refresh credentials if CredentialRefreshNeededError occurs
        print("Refreshing AWS credentials...")
        session.get_credentials().refresh()

# Define a route for Prometheus to scrape the metrics
@app.route('/metrics')
def metrics():
    return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)

def job():
    print("Updating metrics...")
    update_metrics()

schedule.every(30).seconds.do(job)

def run_flask_app():
    app.run(port=5000)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()

    while True:
        schedule.run_pending()
        time.sleep(1) 