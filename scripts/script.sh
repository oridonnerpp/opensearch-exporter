python3 auth.py | sed -e "s/'/\"/g" -e "s/None/\"None\"/g" -e "s/False/\"False\"/g" | jq .

sudo docker run \
 -e "AWS_DEFAULT_REGION=us-east-2" \
 -e "AWS_ACCESS_KEY_ID=ASIATJLB5QSXSZ7TT4CB" \
 -e "AWS_SECRET_ACCESS_KEY=FX1+z/QHo5buqEULrdvYwvL/hk8S/eUqpwmpMR7A" \
 -e "AWS_SESSION_TOKEN=FwoGZXIvYXdzEN3//////////wEaDLaJhKvn9BQT2zimpCKsAqfXTOrTP4UQYgF9wFizqPL2y6hwNHqRaP/ZDHoBMi+vSQVprcemIgLcmM+RVIhVoyDQ5ueglMQYOnYurd3SK76NQPsM3YsQZCoizntwRtfAE8saf3BUniJlMYoK5RTfTHwYayvqVhWPUDrGXj1a0qND+KsQ83RCujCuaMoPfCKi75qm0iMZh3WMuhwKDh6ueQLZqcjiyieo7t9ilwWPsS+fFlgSYgkZiB98rOGzpVIXEQlI6tcQ1CqEaOHFelnmk7BWfRrqymFp+x3OwRfpChp1V5U24zC2lUjthxjnYCl3+NVSPyOQEs76Mfoev7EFAYKpLv3sAT7VUEikQJN0ta0e7rHnksa4H7lfXkZrxa9EDLPvRaKhGi82Y/Scbdis4jI6h4VBjxomRMpnGCi1/46tBjIq6A7yeLSI/jiZ081d4pnxxzUjyc2YLciQzjx6KWolEikLMDkOnYnhIUy9" \
 -e "QUERY_TIME_RANGE=5" -e "QUERY_TIME_LAG=20" -e "QUERY_TIME_REFRESH=50" \
 -p 5000:5000 fetch:1.0.3

