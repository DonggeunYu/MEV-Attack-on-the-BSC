import pulumi
import pulumi_gcp as gcp

# Import the program's configuration settings.
config = pulumi.Config("gcp")
project = config.require("project")
region = config.require("region")
zone = config.require("zone")

makima = pulumi.Config("makima")
node_machine_type = makima.require("nodeMachineType")

ethereum_node_network = gcp.compute.Network("ethereum-node-network", project=project)
ethereum_node_subnetwork = gcp.compute.Subnetwork(
    "ethereum-node-subnetwork",
    ip_cidr_range="10.0.0.0/16",
    region=region,
    network=ethereum_node_network.id,
    opts=pulumi.ResourceOptions(depends_on=[ethereum_node_network]),
)
ethereum_node_firewall = gcp.compute.Firewall(
    "ethereum-node-firewall",
    network=ethereum_node_network.id,
    priority=1000,
    direction="INGRESS",
    target_tags=["ethereum-node"],
    source_ranges=["0.0.0.0/0"],
    allows=[
        {"protocol": "tcp", "ports": [30303, 8545, 8546, 9000]},
        {"protocol": "udp", "ports": [30303, 9000]},
    ],
)
ethereum_node_firewall_for_ssh = gcp.compute.Firewall(
    "ethereum-node-firewall-for-ssh",
    network=ethereum_node_network.id,
    priority=1000,
    direction="INGRESS",
    target_tags=["ethereum-node"],
    source_ranges=["0.0.0.0/0"],
    allows=[
        {"protocol": "tcp", "ports": [22]},
    ],
)
pulumi.export("ethereum_node_network", ethereum_node_network)
pulumi.export("ethereum_node_subnetwork", ethereum_node_subnetwork)
pulumi.export("default_firewall", ethereum_node_firewall)
pulumi.export("ssh_firewall", ethereum_node_firewall_for_ssh)

# Service Account for VM
ethereum_node_service_account = gcp.serviceaccount.Account(
    "ethereum-node-service-account",
    account_id="ethereum-node-service-account",
    display_name="Service Account for ethereum-node",
    project=project,
)

ethereum_node_service_account_email = ethereum_node_service_account.email.apply(
    lambda email: f"serviceAccount:{email}"
)
pulumi.export("ethereum_node_service_account", ethereum_node_service_account)
role_for_ethereum_node_service_account = [
    "roles/compute.osLogin",
    "roles/servicemanagement.serviceController",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
    "roles/artifactregistry.reader",
]
for role in role_for_ethereum_node_service_account:
    gcp.projects.IAMBinding(
        f"ethereum-node-service-account-{role}",
        members=[ethereum_node_service_account_email],
        role=role,
        project=project,
        opts=pulumi.ResourceOptions(depends_on=[ethereum_node_service_account]),
    )

# Create a VM
node_internal_ip = "10.0.1.0"
ethereum_node_internal_ip = gcp.compute.Address(
    "ethereum-node-internal-ip",
    address_type="INTERNAL",
    subnetwork=ethereum_node_subnetwork.id,
    address=node_internal_ip,
    region=region,
)

ethereum_node_disk_name = "ethereum-node-disk"
ethereum_node_disk = gcp.compute.Disk(
    ethereum_node_disk_name,
    size=1280,
    type="pd-ssd",
    zone=zone,
    opts=pulumi.ResourceOptions(
        protect=True, depends_on=[ethereum_node_service_account]
    ),
)
image_name = "asia-northeast3-docker.pkg.dev/makima-dev/docker-registry/node-ethereum:cbd50f7f28f49f7c3b9f4f664812cd750c76b853"
container_declaration = f"""spec:
            containers:
            - name: ethereum-node
              image: '{image_name}'
              volumeMounts:
              - name: {ethereum_node_disk_name}
                mountPath: /data
                readOnly: false
            volumes:
            - name: {ethereum_node_disk_name}
              gcePersistentDisk:
                pdName: {ethereum_node_disk_name}
                fsType: ext4
            restartPolicy: Always"""
ethereum_node_service_account_email = ethereum_node_service_account.email.apply(
    lambda email: f"{email}"
)
instance = gcp.compute.Instance(
    "ethereum-node",
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
        "email": ethereum_node_service_account_email,
        "scopes": ["cloud-platform"],
    },
    tags=ethereum_node_firewall.target_tags,
    network_interfaces=[
        gcp.compute.InstanceNetworkInterfaceArgs(
            network=ethereum_node_network.id,
            subnetwork=ethereum_node_subnetwork.id,
            network_ip=ethereum_node_internal_ip.address,
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
            source=ethereum_node_disk.id,
            device_name=ethereum_node_disk_name,
            mode="READ_WRITE",
        )
    ],
    allow_stopping_for_update=True,
    opts=pulumi.ResourceOptions(
        delete_before_replace=True,
        depends_on=[
            ethereum_node_network,
            ethereum_node_subnetwork,
            ethereum_node_firewall,
            ethereum_node_firewall_for_ssh,
            ethereum_node_service_account,
            ethereum_node_internal_ip,
            ethereum_node_disk,
        ],
    ),
)
pulumi.export("ethereum_node", instance)
