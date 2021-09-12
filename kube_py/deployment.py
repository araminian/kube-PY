import json
from kubernetes import client
import kubernetes


def getDeployment(namespace,deploymentName) -> dict:

    appsAPI = client.AppsV1Api()
    deploymentData = {}
    try:
        deployment = appsAPI.read_namespaced_deployment(name=deploymentName,namespace=namespace)
        deploymentData = {
                'Namespace': deployment.metadata.namespace,
                'Name': deployment.metadata.name,
                'Labels': deployment.metadata.labels,
                'Selector': deployment.spec.selector,
                'Pod-Labels': deployment.spec.template.metadata.labels
            }
    except kubernetes.client.exceptions.ApiException as e:
        if (e.status == 404):
            return {"ErrorCode": '404', 'ErrorMsg': 'The Deployment {0} not found.'.format(deploymentName)}
        else:
            return {"ErrorCode": '500', 'ErrorMsg': e.reason}
    
    return deploymentData



def getDeploymentsInNamespace(namespace) -> list:

    appsAPI = client.AppsV1Api()
    
    result = appsAPI.list_namespaced_deployment(namespace=namespace)
    jsonOutput = []

    for deployment in result.items:

        deploymentData = {
            'Namespace': deployment.metadata.namespace,
            'Name': deployment.metadata.name,
            'Labels': deployment.metadata.labels,
            'Selector': deployment.spec.selector,
            'Pod-Labels': deployment.spec.template.metadata.labels
        }

        
        jsonOutput.append(deploymentData)

    return jsonOutput


# Get ALL Deployments in all Namespaces 
def getAllDeployments() -> list:

    appsAPI = client.AppsV1Api()
    
    result = appsAPI.list_deployment_for_all_namespaces()
    jsonOutput = []

    for deployment in result.items:

        deploymentData = {
            'Namespace': deployment.metadata.namespace,
            'Name': deployment.metadata.name,
            'Labels': deployment.metadata.labels,
            'Selector': deployment.spec.selector,
            'Pod-Labels': deployment.spec.template.metadata.labels
        }

        
        jsonOutput.append(deploymentData)


    return jsonOutput


