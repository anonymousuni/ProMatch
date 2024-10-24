import random
import re
import subprocess
import sys
import os
import requests
import time
import json
import yaml
from subprocess import call
import numpy
import logging
from kubernetes import client, config, watch

#from prometheus_api_client import PrometheusConnect
#prom = PrometheusConnect(url="http://localhost:9090", disable_ssl=True)

config.load_kube_config()
v1=client.CoreV1Api()

def nodes_available() -> list:
    ready_nodes = []
    for n in v1.list_node().items:
            for status in n.status.conditions:
                if status.status == "True" and status.type == "Ready":
                    ready_nodes.append(n.metadata.name)
    return ready_nodes

def scheduler(pod, node, namespace="default"):
    # print("start binding")
    try:
        target = client.V1ObjectReference()
        target.kind = "Node"
        target.apiVersion = "v1"
        target.api_version = 'v1'
        target.name = node
        #print("Target object: ", target)
        if target.name != '':
            meta = client.V1ObjectMeta()
            meta.name = pod.metadata.name
            body = client.V1Binding(target=target, metadata=meta)
            v1.create_namespaced_binding(namespace, body, _preload_content=False)
            print(meta.name, " scheduled on ", node)
        else:
           print(pod.metadata.name, " not scheduled")
    except client.rest.ApiException as e:
        print(json.loads(e.body)['message'])
        print("------------------------------------------")
    return

def main():
    #query_cpu_container = prom.custom_query(query="sort_desc((container_cpu_user_seconds_total))")
    #print(query_cpu_container)
    print(nodes_available())
    print()
    call(["minikube", "kubectl", "--", "apply", "-f", "micro-deployment.yaml"])
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_pod, "default"):
        ###regex = "\s*'status':\s*'(True)',\s*'type': '(PodScheduled)'"
        ###check = re.search(regex,str(event['object'].status.conditions))
        #print ("Hey there!")
        #print(event['object'])
        #print(v1.list_namespaced_pod(namespace='default', label_selector='.status.conditions'.format(name))
        if event['object'].status.phase == "Pending" and event['object'].spec.scheduler_name == "prematch-sched":
            try:
                print("------------------------------------------")
                print("scheduling pod ", event['object'].metadata.name)
                y=random.randrange(1,2,1)
                #print(nodes_available())
                res = scheduler(event['object'], (nodes_available())[y])
                #break
            except client.rest.ApiException as e:
                print (json.loads(e.body)['message'])
if __name__ == '__main__':
    start_time = time.monotonic()
    main()
    elapsed_time = numpy.round(time.monotonic() - start_time , 5)
    print ("=====================================================================")
    print ("Algorithm execution time: {} second(s)".format(elapsed_time))
    print ("=====================================================================")
