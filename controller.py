import yaml
import json

from kubernetes import client, config, watch


def gen_runner_job(image, command):
    s = """apiVersion: batch/v1
kind: Job
metadata:
  name: %s
spec:
  template:
    spec:
      containers:
      - name: %s
        image: %s
        command: ["date"]
      restartPolicy: Never
  backoffLimit: 4""" % (image,image, image)
    return yaml.load(s)


if __name__ == "__main__":
    config.load_kube_config()
    configuration = client.Configuration()
    api_client = client.api_client.ApiClient(configuration=configuration)
    v1 = client.ApiextensionsV1beta1Api(api_client)
    batchv1 = client.BatchV1Api(api_client)
    #current_crds = [x['spec']['names']['kind'].lower() for x in v1.list_custom_resource_definition().to_dict()['items']]
    crds = client.CustomObjectsApi(api_client)

    print("Waiting for Runners to come up...")
    resource_version = ''
    while True:
        stream = watch.Watch().stream(crds.list_cluster_custom_object, "iberryful.com", "v1", "runners",
                                      resource_version=resource_version)
        for event in stream:
            obj = event["object"]
            operation = event['type']
            spec = obj.get("spec")

            if not spec:
                continue

            metadata = obj.get("metadata")
            name = metadata['name']
            print("Got %s on %s" % (operation, name))
            if operation not in ("ADDED", "DELETED"):
                continue
            image = spec['image']
            command = spec['command']
            namespace = metadata['namespace']

            runner_job_def = gen_runner_job(image, command)
            print(runner_job_def)
            if operation == 'ADDED':
                batchv1.create_namespaced_job(namespace, body=runner_job_def )
            elif operation == 'DELETED':
                batchv1.delete_namespaced_job(name, namespace, body=client.V1DeleteOptions())
            print("Handling %s on %s" % (operation, name))

    