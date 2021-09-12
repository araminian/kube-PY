from os import name
from kubernetes import client
from kube_py.deployment import getDeployment
import kubernetes


def getPodsInDeployment(namespace,deployment) -> list:

    deploymentObject = getDeployment(namespace=namespace,deploymentName=deployment)

    if (type(deploymentObject) == dict and 'ErrorCode' in deploymentObject):
        return deploymentObject
    
    deploymentPodLabels = deploymentObject['Pod-Labels']
    v1API = client.CoreV1Api()

    lableList = []
    for key,value in deploymentPodLabels.items():
        lableList.append("{0}={1}".format(key,value))

    selector = ",".join(lableList)

    
    podsList = []
    try:
        pods = v1API.list_namespaced_pod(namespace=namespace,label_selector=selector)

        for pod in pods.items:


            PodData = {
                    'Namespace': pod.metadata.namespace,
                    'Name': pod.metadata.name,
                    'Labels': pod.metadata.labels,
                    'IP': pod.status.pod_ip
                }
            podsList.append(PodData)
    except kubernetes.client.exceptions.ApiException as e:
        return {"ErrorCode": '500', 'ErrorMsg': e.reason}
    
    return podsList


def getPod(namespace,podName) -> dict:
    PodData = {}
    try:
        v1API = client.CoreV1Api()
        pod = v1API.read_namespaced_pod(name=podName,namespace=namespace)
        PodData = {
                'Namespace': pod.metadata.namespace,
                'Name': pod.metadata.name,
                'Labels': pod.metadata.labels,
            }
    except kubernetes.client.exceptions.ApiException as e:
        if (e.status == 404):
            return {"ErrorCode": '404', 'ErrorMsg': 'The Pod {0} not found.'.format(podName)}
        else:
            return {"ErrorCode": '500', 'ErrorMsg': e.reason}
    return PodData


def getPodsInNamespace(namespace) -> list:

    v1API = client.CoreV1Api()

    result = v1API.list_namespaced_pod(namespace=namespace)

    jsonOutput = []
    for pod in result.items:
        PodData = {
            'Namespace': pod.metadata.namespace,
            'Name': pod.metadata.name,
            'Labels': pod.metadata.labels,
        }
        jsonOutput.append(PodData)

    return jsonOutput



def getAllPods() -> list:

    v1API = client.CoreV1Api()

    result = v1API.list_pod_for_all_namespaces()

    jsonOutput = []
    for pod in result.items:
        PodData = {
            'Namespace': pod.metadata.namespace,
            'Name': pod.metadata.name,
            'Labels': pod.metadata.labels,
        }
        jsonOutput.append(PodData)

    return jsonOutput

