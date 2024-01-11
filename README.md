Execute the following command after you login to AWS testing environment:
`python3 refresh.py`

_Flask_ web server will be launched on your local machine where you can view all _OpenSearch_ parmas exposed by _Prometheus_ client.


The data is set as follows:
metric{label="label value"} metric_value 

4 metrics are tracked (Prometheus Gauges), one label is defined - "function" label, for example:
```
Max_float_1{function="run_decisions"} 9.590666
Median_float_1{function="_static_scan_and_unpacking"} 7.78495
Average_float_1{function="unpack"} 3.0639
function_count{function="start_remote_scan"} 907.
```
