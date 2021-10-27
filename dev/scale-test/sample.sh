#!/bin/bash

requested=${1:-0}
node_count=${2:-1}
required_scale=$((requested / node_count))
out_dir="out/sample"
result_file_path="$out_dir/result.txt"

mkdir -p $out_dir
echo "" > $result_file_path

ready=$(kubectl get pods -o custom-columns=NAMESPACE:metadata.namespace,POD:metadata.name,PodIP:status.podIP,READY:status.containerStatuses[*].ready | grep -c true)


start_time=$(date +%s)
echo "0s -- $ready ready pods"
echo "0,$ready" >> $result_file_path

cmd=$(kubectl scale --replicas="$required_scale" statefulset --all)
echo "$cmd"
while [ "$ready" -ne "$requested" ]; do
  sleep 1
  now=$(date +%s)
  ready=$(kubectl get pods -o custom-columns=NAMESPACE:metadata.namespace,POD:metadata.name,PodIP:status.podIP,READY:status.containerStatuses[*].ready | grep -c true)
  echo "$(( now - start_time ))s -- $ready ready pods"
  echo "$(( now - start_time )),$ready" >> $result_file_path
done
now=$(date +%s)
echo "$(( now - start_time ))s -- $requested ready pods"
echo "$(( now - start_time )),$ready" >> $result_file_path
echo "done"