POST /ops-logs-*/_search
{
  "aggs": {
    "2": {
      "terms": {
        "field": "str_1",
        "order": {
          "1": "desc"
        },
        "size": 20
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
          "exists": {
            "field": "float_1"
          }
        },
        {
          "match_phrase": {
            "kubernetes.namespace": "eu"
          }
        },
        {
          "match_phrase": {
            "kubernetes.container.name": "mantis-worker-url"
          }
        },
        {
          "match_phrase": {
            "action": "timer"
          }
        },
        {
          "range": {
            "@timestamp": {
              "gte": "2024-02-04T10:51:30.000Z",
              "lte": "2024-02-04T11:51:30.000Z",
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