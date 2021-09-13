from kube_py.pod import getAllPods
from os import name
from kubernetes import client, config
from kube_py.deployment import *
from kube_py.pod import *

# config.load_incluster_config()

config.load_kube_config()

# result = getPodsInDeployment(namespace='default',deployment='nginx-deployment')
# print(result)

script = 'while true; do echo "foo"; sleep 2; done'
#script = 'ifconfig'
commandresult = runScriptInPod(namespace='default',pod='nginx-deployment-66b6c48dd5-2snv4',script=script)
print(commandresult)