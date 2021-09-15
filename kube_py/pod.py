from os import name, path
from kubernetes import client
from kube_py.deployment import getDeployment
import kubernetes
from kubernetes.stream import stream
import time
import tarfile
from tempfile import TemporaryFile
import pathlib

# Copy File from Pod to Host(Pod) : PULL
def copyFileFromPod(namespace,pod,sourceFile,destinationDir,podTimeout=1):
    podWaitTimeout = time.time() + 60*podTimeout
    # Check if the pod exists
    podResult  = getPod(namespace=namespace,podName=pod)
    if (type(podResult) == dict and 'ErrorCode' in podResult):
        
        return podResult
    
    v1API = client.CoreV1Api()

    while True:
            resp = v1API.read_namespaced_pod(name=pod,
                                                    namespace=namespace)
            if resp.status.phase == 'Running':
                break
            if (time.time() > podWaitTimeout):
                return {"ErrorCode":"601","ErrorMsg": "Pod is not running after {0} minutes.".format(podTimeout)}
            time.sleep(1)
    print("Pod {0} is ready ....".format(pod))
    print('copying pod -> client')
    filePath = pathlib.PurePath(sourceFile)
    fileName = filePath.parts[-1]
    fileParent = filePath.parent
    
    exec_command = ['tar', 'cf', '-', '-C' , str(fileParent) , str(fileName)]
    
    with TemporaryFile() as buffer:

        resp = stream(v1API.connect_get_namespaced_pod_exec, pod, namespace,
                    command=exec_command,
                    stderr=True, stdin=True,
                    stdout=True, tty=False,
                    _preload_content=False)

        while resp.is_open():
            resp.update(timeout=1)
            if resp.peek_stdout():
                out = resp.read_stdout()
                print("bytes received: %s" % len(out))
                buffer.write(out.encode())
            if resp.peek_stderr():
                print("STDERR: %s" % resp.read_stderr())
                return {"ErrorCode":"666","ErrorMsg": "Copy fail."}
        resp.close()

        buffer.flush()
        buffer.seek(0)

        with tarfile.open(fileobj=buffer, mode='r:') as tar:
            tar.extractall(destinationDir)
    return {"StatusCode":"200"}

# Copy File from Host(Pod) to Pod : PUSH
def copyFileToPod(namespace,pod,source,destinationDir,podTimeout=1):

    podWaitTimeout = time.time() + 60*podTimeout
    # Check if the pod exists
    podResult  = getPod(namespace=namespace,podName=pod)
    if (type(podResult) == dict and 'ErrorCode' in podResult):
        
        return podResult
    
    v1API = client.CoreV1Api()

    while True:
            resp = v1API.read_namespaced_pod(name=pod,
                                                    namespace=namespace)
            if resp.status.phase == 'Running':
                break
            if (time.time() > podWaitTimeout):
                return {"ErrorCode":"601","ErrorMsg": "Pod is not running after {0} minutes.".format(podTimeout)}
            time.sleep(1)
    print("Pod {0} is ready ....".format(pod))
    print('copying client -> pod')


    exec_command = ['tar', 'xvf', '-', '-C', destinationDir]

    resp = stream(v1API.connect_get_namespaced_pod_exec, pod, namespace,
                command=exec_command,
                stderr=True, stdin=True,
                stdout=True, tty=False,
                _preload_content=False)

    source_file = source
    fileName = source_file.split('/')[-1]
    with TemporaryFile() as tar_buffer:
        with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
            tar.add(source_file,arcname=fileName)

        tar_buffer.seek(0)
        commands = []
        commands.append(tar_buffer.read())

        while resp.is_open():
            resp.update(timeout=1)
            if resp.peek_stdout():
                print("STDOUT: %s" % resp.read_stdout())
            if resp.peek_stderr():
                print("STDERR: %s" % resp.read_stderr())
                resp.close()
                return {"ErrorCode":"666","ErrorMsg": "Copy fail."}
            if commands:
                c = commands.pop(0)
                resp.write_stdin(c)
            else:
                break
        resp.close()
        return {"StatusCode":"200"}

def runScriptInPod(namespace,pod,script,podTimeout=1,scriptTimeout=1,shell='/bin/sh'):
    
    podWaitTimeout = time.time() + 60*podTimeout
    # Check if the pod exists
    podResult  = getPod(namespace=namespace,podName=pod)
    if (type(podResult) == dict and 'ErrorCode' in podResult):
        
        return podResult
    
    v1API = client.CoreV1Api()

    while True:
            resp = v1API.read_namespaced_pod(name=pod,
                                                    namespace=namespace)
            if resp.status.phase == 'Running':
                break
            if (time.time() > podWaitTimeout):
                return {"ErrorCode":"601","ErrorMsg": "Pod is not running after {0} minutes.".format(podTimeout)}
            time.sleep(1)
    print("Pod {0} is ready ....".format(pod))
    print("Run script {0} ....".format(script))
     
    exec_command = [shell, '-c', script]

    resp = stream(v1API.connect_get_namespaced_pod_exec,
                  pod,
                  namespace,
                  command=exec_command,
                  stderr=True, stdin=False,
                  stdout=True, tty=False,
                  _preload_content=False)


    scriptWaitTimeout = time.time() + 60*scriptTimeout
    while resp.is_open():
            resp.update(timeout=1)

            if (time.time() > scriptWaitTimeout):
                resp.close()
                return {"ErrorCode":"666","ErrorMsg": "Script timeout."}

            if resp.peek_stdout():
                print("STDOUT: %s" % resp.read_stdout())
            if resp.peek_stderr():
                print("STDERR: %s" % resp.read_stderr())

    resp.close()

    if resp.returncode != 0:
        return {"ErrorCode":"666","ErrorMsg": "Script executes fail."}
    else:
        return {"StatusCode":"200"}

    


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

