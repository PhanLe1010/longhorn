from os import times
import time
from re import S
import sys
import asyncio
import logging
from pathlib import Path
from asyncio.tasks import sleep
from kubernetes import client, config, watch

NAMESPACE = "default"
TEMPLATE_FILE = "statefulset.yaml"
STS_PREFIX = "sts-"
IMAGE = "phanle1010/ubuntu:fio"
KUBE_CONFIG = None
KUBE_CONTEXT = None

REPLICA_COUNT=1


def get_node_name_list():
    v1 = client.CoreV1Api()
    node_names = []
    ret = v1.list_node(watch=False)
    for i in ret.items:
        if i.metadata.labels.get("node-role.kubernetes.io/worker", False) or i.metadata.labels.get("node-role.longhorn.io/worker", False):
         node_names.append(i.metadata.name)
    return node_names    

def create_sts_objects():
    # @NODE_NAME@ - schedule each sts on a dedicated node
    # @STS_NAME@ - also used for the volume-name
    sts_objects = []
    for node_name in get_node_name_list():
        sts_objects.append(create_sts_spec(node_name))
    return sts_objects

def create_sts_yaml(node_name):
    content = Path(TEMPLATE_FILE).read_text()
    content = content.replace("@NODE_NAME@", node_name)
    sts_name = STS_PREFIX + node_name
    content = content.replace("@STS_NAME@",  sts_name)
    file = Path("out/" + sts_name + ".yaml")
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content)
    logging.info("created %s" % sts_name)

# create_sts_spec returns a list of need to deploy statefulsets
def create_sts_spec(node_name) :
    sts_name = STS_PREFIX + node_name
    container = client.V1Container(
        name=sts_name,
        image=IMAGE,
        command=["/bin/bash"],
        args=["-c", "while :; do fio --name=simulate-workload-io --ioengine=libaio --direct=1 --readwrite=randrw --bs=128k --size=8G --io_size=5G --filename=/mnt/"+sts_name+"/fio_test_file --iodepth=4 --rwmixread=75; sync; sleep 15; done"],
        liveness_probe=client.V1Probe(
            _exec=client.V1ExecAction(
                command=["ls", "/mnt/"+sts_name]
            ),
            initial_delay_seconds=5,
            period_seconds=5
        ),
        volume_mounts=[client.V1VolumeMount(
            name=sts_name,
            mount_path="/mnt/"+sts_name
        )]
    )

    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app":sts_name}),
        spec=client.V1PodSpec(
            node_name=node_name,
            restart_policy="Always",
            termination_grace_period_seconds=10,
            containers=[container],

        )
    )

    spec = client.V1StatefulSetSpec(
        replicas=0,
        service_name=sts_name,
        selector=client.V1LabelSelector(
            match_labels={"app":sts_name}
        ),
        template=template,
        volume_claim_templates=[client.V1PersistentVolumeClaim(
            metadata=client.V1ObjectMeta(name=sts_name),
            spec=client.V1PersistentVolumeClaimSpec(
                access_modes=["ReadWriteOnce"],
                storage_class_name="longhorn",
                resources=client.V1ResourceRequirements(
                    requests={"storage":"10Gi"}
                )
            )
        )]
    )

    statefulset=client.V1StatefulSet(
        api_version="apps/v1",
        kind="StatefulSet",
        metadata=client.V1ObjectMeta(name=sts_name),
        spec=spec
    )
    statefulset.spec.replicas

    return statefulset

def create_statefulsets(api, sts_objects):
    for sts in sts_objects:
        api.create_namespaced_stateful_set(namespace="default", body=sts)

def scale_statefulsets(api, sts_objects, n):
    for sts in sts_objects:
        sts = api.read_namespaced_stateful_set(name=sts.metadata.name, namespace="default")
        sts.spec.replicas = n
        api.patch_namespaced_stateful_set(name=sts.metadata.name, namespace="default", body=sts)
        
        

async def watch_pods_async():
    log = logging.getLogger('pod_events')
    log.setLevel(logging.INFO)
    v1 = client.CoreV1Api()
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_pod, namespace=NAMESPACE):
        process_pod_event(log, event)
        await asyncio.sleep(0)


def process_pod_event(log, event):
    log.info("Event: %s %s %s" % (event['type'], event['object'].kind, event['object'].metadata.name))
    if 'ADDED' in event['type']:
        pass
    elif 'DELETED' in event['type']:
        pass
    else:
        pass


async def watch_pvc_async():
    log = logging.getLogger('pvc_events')
    log.setLevel(logging.INFO)
    v1 = client.CoreV1Api()
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_persistent_volume_claim, namespace=NAMESPACE):
        process_pvc_event(log, event)
        await asyncio.sleep(0)


def process_pvc_event(log, event):
    log.info("Event: %s %s %s" % (event['type'], event['object'].kind, event['object'].metadata.name))
    if 'ADDED' in event['type']:
        pass
    elif 'DELETED' in event['type']:
        pass
    else:
        pass


async def watch_va_async():
    log = logging.getLogger('va_events')
    log.setLevel(logging.INFO)
    storage = client.StorageV1Api()
    w = watch.Watch()
    for event in w.stream(storage.list_volume_attachment):
        process_va_event(log, event)
        await asyncio.sleep(0)


def process_va_event(log, event):
    log.info("Event: %s %s %s" % (event['type'], event['object'].kind, event['object'].metadata.name))
    if 'ADDED' in event['type']:
        pass
    elif 'DELETED' in event['type']:
        pass
    else:
        pass


if __name__ == '__main__':
    # setup the monitor
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(stream=sys.stdout,
                        level=logging.INFO,
                        format=log_format)
    config.load_kube_config(config_file=KUBE_CONFIG,
                            context=KUBE_CONTEXT)

    # create the sts deployment files
    sts_objects = create_sts_objects()

    apps_v1 = client.AppsV1Api()
    create_statefulsets(apps_v1, sts_objects)
    print("Created %d statefulsets" % (len(sts_objects)))

    print("sleeping for 30s")
    time.sleep(30)

    scale_statefulsets(apps_v1, sts_objects, REPLICA_COUNT)
    print("Scaled %d statefulsets so that each has %d replicas" % (len(sts_objects), REPLICA_COUNT))

    # monitor the result and draw the graph in real time
    # Also make sure the graph is persisted in case something break in the middle 
    # Make a different command for: deploy, monitor, cleanup 
    

    logging.info("scale-test started")

    # datastructures to keep track of the timings
    # TODO: process events and keep track of the results
    #       results should be per pod/volume
    #       information to keep track: pod index per sts
    #       volume-creation time per pod
    #       volume-attach time per pod
    #       volume-detach time per pod
    # pvc_to_va_map = dict()
    # pvc_to_pod_map = dict()
    # results = dict()

    # start async event_loop
    # event_loop = asyncio.get_event_loop()
    # event_loop.create_task(watch_pods_async())
    # event_loop.create_task(watch_pvc_async())
    # event_loop.create_task(watch_va_async())
    # event_loop.run_forever()
    logging.info("scale-test-finished")

