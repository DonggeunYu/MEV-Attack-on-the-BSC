import pulumi
import pulumi_gcp as gcp

# Import the program's configuration settings.
config = pulumi.Config("gcp")
project = config.require("project")
region = config.require("region")
zone = config.require("zone")

makima = pulumi.Config("makima")
node_machine_type = makima.require("nodeMachineType")

node_network = gcp.compute.Network("node-bsc-network", project=project)
node_subnetwork = gcp.compute.Subnetwork(
    "node-bsc-subnetwork",
    ip_cidr_range="10.0.0.0/16",
    region=region,
    network=node_network.id,
    opts=pulumi.ResourceOptions(depends_on=[node_network]),
)
node_firewall = gcp.compute.Firewall(
    "node-bsc-firewall",
    network=node_network.id,
    priority=1000,
    direction="INGRESS",
    target_tags=["node-bsc"],
    source_ranges=["0.0.0.0/0"],
    allows=[
        {"protocol": "tcp", "ports": [30303, 8545, 8546, 9000]},
        {"protocol": "udp", "ports": [30303, 9000]},
    ],
)
node_firewall_for_ssh = gcp.compute.Firewall(
    "node-bsc-firewall-for-ssh",
    network=node_network.id,
    priority=1000,
    direction="INGRESS",
    target_tags=["node-bsc"],
    source_ranges=["0.0.0.0/0"],
    allows=[
        {"protocol": "tcp", "ports": [22]},
    ],
)
pulumi.export("bsc_node_network", node_network)
pulumi.export("bsc_node_subnetwork", node_subnetwork)
pulumi.export("default_firewall", node_firewall)
pulumi.export("ssh_firewall", node_firewall_for_ssh)

# Service Account for VM
node_service_account = gcp.serviceaccount.Account(
    "node-bsc-service-account",
    account_id="node-bsc-service-account",
    display_name="Service Account for node-bsc",
    project=project,
)

node_service_account_email = node_service_account.email.apply(
    lambda email: f"serviceAccount:{email}"
)
pulumi.export("node_service_account", node_service_account)
role_for_node_service_account = [
    "roles/compute.osLogin",
    "roles/servicemanagement.serviceController",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
    "roles/artifactregistry.reader",
]
for role in role_for_node_service_account:
    gcp.projects.IAMBinding(
        f"node-bsc-service-account-{role}",
        members=[node_service_account_email],
        role=role,
        project=project,
        opts=pulumi.ResourceOptions(depends_on=[node_service_account]),
    )

# Create a VM
node_internal_ip = "10.0.1.0"
node_internal_ip = gcp.compute.Address(
    "node-bsc-internal-ip",
    address_type="INTERNAL",
    subnetwork=node_subnetwork.id,
    address=node_internal_ip,
    region=region,
)

node_disk_name = "node-bsc-disk"
node_disk = gcp.compute.Disk(
    node_disk_name,
    size=2048,
    type="pd-ssd",
    zone=zone,
    opts=pulumi.ResourceOptions(protect=True, depends_on=[node_service_account]),
)
image_name = "asia-northeast3-docker.pkg.dev/makima-dev/docker-registry/node/bsc:test"
container_declaration = f"""spec:
            containers:
            - name: node-bsc
              image: '{image_name}'
              volumeMounts:
              - name: {node_disk_name}
                mountPath: /data
                readOnly: false
            volumes:
            - name: {node_disk_name}
              gcePersistentDisk:
                pdName: {node_disk_name}
                fsType: ext4
            restartPolicy: Always"""
node_service_account_email = node_service_account.email.apply(lambda email: f"{email}")
instance = gcp.compute.Instance(
    "node-bsc",
    machine_type=node_machine_type,
    zone=zone,
    boot_disk={
        "initializeParams": {
            "image": "cos-cloud/cos-stable",
            "type": "pd-ssd",
            "size": 10,
        }
    },
    service_account={
        "email": node_service_account_email,
        "scopes": ["cloud-platform"],
    },
    tags=node_firewall.target_tags,
    network_interfaces=[
        gcp.compute.InstanceNetworkInterfaceArgs(
            network=node_network.id,
            subnetwork=node_subnetwork.id,
            network_ip=node_internal_ip.address,
            access_configs=[
                gcp.compute.InstanceNetworkInterfaceAccessConfigArgs(
                    nat_ip=gcp.compute.address.Address("address").address,
                    network_tier="PREMIUM",
                )
            ],
            nic_type="GVNIC",
        ),
    ],
    metadata={"gce-container-declaration": container_declaration},
    attached_disks=[
        gcp.compute.InstanceAttachedDiskArgs(
            source=node_disk.id,
            device_name=node_disk_name,
            mode="READ_WRITE",
        )
    ],
    allow_stopping_for_update=True,
    opts=pulumi.ResourceOptions(
        delete_before_replace=True,
        depends_on=[
            node_network,
            node_subnetwork,
            node_firewall,
            node_firewall_for_ssh,
            node_service_account,
            node_internal_ip,
            node_disk,
        ],
    ),
)
pulumi.export("bsc_node", instance)
