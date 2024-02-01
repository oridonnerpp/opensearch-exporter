python3 auth.py | sed -e "s/'/\"/g" -e "s/None/\"None\"/g" -e "s/False/\"False\"/g" | jq .

sudo docker run \
 -e "AWS_DEFAULT_REGION=us-east-2" \
 -e "AWS_ACCESS_KEY_ID=ASIATJLB5QSXSZ7TT4CB" \
 -e "AWS_SECRET_ACCESS_KEY=FX1+z/QHo5buqEULrdvYwvL/hk8S/eUqpwmpMR7A" \
 -e "AWS_SESSION_TOKEN=FwoGZXIvYXdzEN3//////////wEaDLaJhKvn9BQT2zimpCKsAqfXTOrTP4UQYgF9wFizqPL2y6hwNHqRaP/ZDHoBMi+vSQVprcemIgLcmM+RVIhVoyDQ5ueglMQYOnYurd3SK76NQPsM3YsQZCoizntwRtfAE8saf3BUniJlMYoK5RTfTHwYayvqVhWPUDrGXj1a0qND+KsQ83RCujCuaMoPfCKi75qm0iMZh3WMuhwKDh6ueQLZqcjiyieo7t9ilwWPsS+fFlgSYgkZiB98rOGzpVIXEQlI6tcQ1CqEaOHFelnmk7BWfRrqymFp+x3OwRfpChp1V5U24zC2lUjthxjnYCl3+NVSPyOQEs76Mfoev7EFAYKpLv3sAT7VUEikQJN0ta0e7rHnksa4H7lfXkZrxa9EDLPvRaKhGi82Y/Scbdis4jI6h4VBjxomRMpnGCi1/46tBjIq6A7yeLSI/jiZ081d4pnxxzUjyc2YLciQzjx6KWolEikLMDkOnYnhIUy9" \
 -e "QUERY_TIME_RANGE=5" -e "QUERY_TIME_LAG=20" -e "QUERY_TIME_REFRESH=50" \
 -p 5000:5000 fetch:1.0.3

# install botosession
pip3 install git+https://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@github.com/perceptionpoint/botosession.git

# upload docker image to ECR
sudo docker build -t fetch:1.2.2 . 
sudo docker tag fetch:1.2.2 226228012207.dkr.ecr.us-east-1.amazonaws.com/opensearch-exporter:1.2.2
sudo docker tag fetch:1.2.2 226228012207.dkr.ecr.us-east-1.amazonaws.com/opensearch-exporter:latest
aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin 226228012207.dkr.ecr.us-east-1.amazonaws.com
sudo docker push 226228012207.dkr.ecr.us-east-1.amazonaws.com/opensearch-exporter:1.2.2
sudo docker push 226228012207.dkr.ecr.us-east-1.amazonaws.com/opensearch-exporter:latest

# restart deployment
kubectl delete deploy opensearch-exporter-deployment -n mantis-system
kubectl apply -f k8s/exporter.yaml 
kubectl get pods -n mantis-system | grep opensearch
# log into pod
kubectl exec -it opensearch-exporter-deployment-5564ffb9f6-jfl6x -n mantis-system -- bash
# pod logs