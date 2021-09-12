from kube_py.pod import getAllPods
from os import name
from kubernetes import client, config
from kube_py.deployment import *
from kube_py.pod import *

# config.load_incluster_config()

config.load_kube_config()

result = getPodsInDeployment(namespace='kube-system',deployment='coredns')
print(result)

