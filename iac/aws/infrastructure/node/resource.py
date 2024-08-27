import json
import pulumi
import pulumi_aws as aws
import pulumi_aws_native as aws_native

config = pulumi.Config("aws")
region = config.require("region")


class ECR(pulumi.ComponentResource):
    repository: aws.ecr.Repository

    def __init__(self, name, opts=None):
        super().__init__("node:Repository", name, {}, opts)

        image_scanning_configuration = aws.ecr.RepositoryImageScanningConfigurationArgs(
            scan_on_push=True
        )
        self.repository = aws.ecr.Repository(
            resource_name=f"{name}-repository",
            name=f"{name.replace('-', '/')}"[:-4],
            image_scanning_configuration=image_scanning_configuration,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs(
            {
                "repository": self.repository,
            }
        )


class VPC(pulumi.ComponentResource):
    vpc: aws.ec2.Vpc
    subnet: aws.ec2.Subnet
    security_group: aws.ec2.SecurityGroup

    def __init__(self, name, index, opts=None):
        super().__init__("node:VPC", name, {}, opts)

        self.vpc = aws.ec2.Vpc(
            f"{name}",
            tags={
                "Name": f"{name}",
            },
            cidr_block=f"10.{index}.0.0/16",
            enable_dns_support=True,  # Enable DNS support.
            enable_dns_hostnames=True,
            opts=pulumi.ResourceOptions(parent=self),
        )
        self.subnet = aws.ec2.Subnet(
            f"{name}-public-subnet",
            tags={
                "Name": f"{name}-public-subnet",
            },
            vpc_id=self.vpc.id,
            cidr_block=f"10.{index}.0.0/24",
            map_public_ip_on_launch=True,
            availability_zone=f"{region}b",
            opts=pulumi.ResourceOptions(parent=self.vpc, depends_on=[self.vpc]),
        )

        igw = aws.ec2.InternetGateway(
            f"{name}-igw",
            vpc_id=self.vpc.id,
            tags={
                "Name": f"{name}-igw",
            },
            opts=pulumi.ResourceOptions(parent=self.vpc, depends_on=[self.vpc]),
        )
        public_route_table = aws.ec2.RouteTable(
            f"{name}-route-table",
            vpc_id=self.vpc.id,
            routes=[
                aws.ec2.RouteTableRouteArgs(
                    cidr_block="0.0.0.0/0",
                    gateway_id=igw.id,
                )
            ],
            tags={
                "Name": f"{name}-route-table",
            },
            opts=pulumi.ResourceOptions(parent=self.vpc, depends_on=[self.vpc, igw]),
        )
        aws.ec2.RouteTableAssociation(
            f"{name}-public-subnet-association",
            subnet_id=self.subnet.id,
            route_table_id=public_route_table.id,
            opts=pulumi.ResourceOptions(
                parent=self.vpc, depends_on=[self.vpc, self.subnet, public_route_table]
            ),
        )

        ingress_rules = [
            aws.ec2.SecurityGroupIngressArgs(
                protocol="ALL",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"],
            )
        ]

        egress_rules = [
            aws.ec2.SecurityGroupEgressArgs(
                protocol="ALL",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"],
            )
        ]

        # Security Group with the Ingress Rules
        self.security_group = aws.ec2.SecurityGroup(
            f"{name}-security-group",
            tags={
                "Name": f"{name}-security-group",
            },
            vpc_id=self.vpc.id,
            ingress=ingress_rules,
            egress=egress_rules,
            opts=pulumi.ResourceOptions(parent=self.vpc, depends_on=[self.vpc]),
        )

        # VPC Endpoint for ECR
        aws.ec2.VpcEndpoint(
            f"{name}-endpoint-ecr-dkr",
            vpc_id=self.vpc.id,
            service_name=f"com.amazonaws.{region}.ecr.dkr",
            vpc_endpoint_type="Interface",
            security_group_ids=[self.security_group.id],
            subnet_ids=[self.subnet.id],
            private_dns_enabled=True,
            tags={"Name": f"{name}-endpoint-ecr-dkr"},
            opts=pulumi.ResourceOptions(
                parent=self.vpc, depends_on=[self.vpc, self.security_group, self.subnet]
            ),
        )
        aws.ec2.VpcEndpoint(
            f"{name}-endpoint-ecr-api",
            vpc_id=self.vpc.id,
            service_name=f"com.amazonaws.{region}.ecr.api",
            vpc_endpoint_type="Interface",
            security_group_ids=[self.security_group.id],
            subnet_ids=[self.subnet.id],
            private_dns_enabled=True,
            tags={"Name": f"{name}-endpoint-ecr-api"},
            opts=pulumi.ResourceOptions(
                parent=self.vpc, depends_on=[self.vpc, self.security_group, self.subnet]
            ),
        )
        aws.ec2.VpcEndpoint(
            f"{name}-endpoint-logs",
            vpc_id=self.vpc.id,
            service_name=f"com.amazonaws.{region}.logs",
            vpc_endpoint_type="Interface",
            security_group_ids=[self.security_group.id],
            subnet_ids=[self.subnet.id],
            private_dns_enabled=True,
            tags={"Name": f"{name}-endpoint-logs"},
            opts=pulumi.ResourceOptions(
                parent=self.vpc, depends_on=[self.vpc, self.security_group, self.subnet]
            ),
        )
        aws.ec2.VpcEndpoint(
            f"{name}-endpoint-s3",
            vpc_id=self.vpc.id,
            service_name=f"com.amazonaws.{region}.s3",
            vpc_endpoint_type="Gateway",
            route_table_ids=[public_route_table.id],
            tags={"Name": f"{name}-endpoint-s3"},
            opts=pulumi.ResourceOptions(parent=self.vpc, depends_on=[self.vpc]),
        )
        aws.ec2.VpcEndpoint(
            f"{name}-endpoint-ssm",
            vpc_id=self.vpc.id,
            service_name=f"com.amazonaws.{region}.ssmmessages",
            vpc_endpoint_type="Interface",
            security_group_ids=[self.security_group.id],
            subnet_ids=[self.subnet.id],
            private_dns_enabled=True,
            tags={"Name": f"{name}-endpoint-ssm"},
            opts=pulumi.ResourceOptions(
                parent=self.vpc, depends_on=[self.vpc, self.security_group, self.subnet]
            ),
        )

        self.register_outputs(
            {
                "vpc": self.vpc,
                "subnet": self.subnet,
                "security_group": self.security_group
            }
        )


class NetworkInterface(pulumi.ComponentResource):
    def __init__(self, name, index, subnet, security_group, opts=None):
        super().__init__("node:NetworkInterface", name, {}, opts)

        self.network_interface = aws.ec2.NetworkInterface(
            f"{name}-eni",
            subnet_id=subnet.id,
            security_groups=[security_group.id],
            private_ips=[
                f"10.{index}.0.10"
            ],
            tags={"Name": f"{name}-eni"},
            opts=pulumi.ResourceOptions(parent=self),
        )
        eip = aws.ec2.Eip(
            f"{name}-eip",
            network_interface=self.network_interface.id,
            tags={"Name": f"{name}-eip"},
            opts=pulumi.ResourceOptions(parent=self, depends_on=[self.network_interface]),
        )

        self.register_outputs(
            {
                "network_interface": self.network_interface,
            }
        )


class DLM(pulumi.ComponentResource):
    def __init__(self, name, opts=None):
        super().__init__("node:LifeCyclePolicy", name, {}, opts)
        assume_role = aws.iam.get_policy_document(
            statements=[
                aws.iam.GetPolicyDocumentStatementArgs(
                    effect="Allow",
                    principals=[
                        aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                            type="Service",
                            identifiers=["dlm.amazonaws.com"],
                        )
                    ],
                    actions=["sts:AssumeRole"],
                )
            ]
        )
        dlm_lifecycle_role = aws.iam.Role(
            f"{name}-role",
            name=f"{name}-role",
            assume_role_policy=assume_role.json,
            opts=pulumi.ResourceOptions(parent=self),
        )

        aws.dlm.LifecyclePolicy(
            f"{name}-policy",
            description="Snapshot for the volume",
            state="ENABLED",
            execution_role_arn=dlm_lifecycle_role.arn,
            tags={"Name": name},
            policy_details=aws.dlm.LifecyclePolicyPolicyDetailsArgs(
                resource_types=["VOLUME"],
                target_tags={"Name": f"{name}-chain-data-volume"},
                schedules=[
                    aws.dlm.LifecyclePolicyPolicyDetailsScheduleArgs(
                        name="snapshot",
                        create_rule=aws.dlm.LifecyclePolicyPolicyDetailsScheduleCreateRuleArgs(
                            cron_expression="cron(0 0 ? * SUN *)"
                        ),
                        retain_rule=aws.dlm.LifecyclePolicyPolicyDetailsScheduleRetainRuleArgs(
                            count=1
                        ),
                        copy_tags=True,
                        tags_to_add={"Name": f"{name}-snapshot"},
                    )
                ],
            ),
            opts=pulumi.ResourceOptions(parent=self, depends_on=[dlm_lifecycle_role]),
        )


class EC2(pulumi.ComponentResource):
    def __init__(self, name, snapshot_id, network_interface, security_group, opts=None):
        super().__init__("node:EC2", name, {}, opts)

        role = aws.iam.Role(
            f"{name}-role",
            assume_role_policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "ec2.amazonaws.com"},
                            "Action": "sts:AssumeRole",
                        }
                    ],
                }
            ),
            opts=pulumi.ResourceOptions(parent=self),
        )

        instance_profile = aws.iam.InstanceProfile(
            f"{name}-instance-profile",
            role=role.name,
            opts=pulumi.ResourceOptions(parent=self, depends_on=[role]),
        )

        key_pair = aws.ec2.KeyPair(
            f"{name}-key-pair",
            key_name=f"{name}-key-pair",
            public_key="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDiGfKSIOxgniSMRrvE+uYzGZ6Kk0758BgRqjh0VWxsdXBYMQCld+npUD9qa9BeBJcmwEm00JMOQwKf8/4AOFv2gpvX3l0y8S8tpM8yMUpQtgqikJPqbTYuxbj/pSXNnnmieZ796v2mH4zTMIXEO1eBX+YO+X8WGkCmtdPZ+AUKJ7DJ4G/A5t3Xf1KH5FOFj+xaA4k9kzAvgiAtos3N7pb+CllHrjF/17fKl76H7D0ctNX955vzWpBmVStNimtrkmWYnc43vMVkzE+0f+CQVtDe/4QSYVCKqHDULejQ62Ao4sm9kCj4sNvt+i6LK8PFGxSw4u0Bp7ovTkhormIRbXFjIrFXf2HfzWCqeP9s5FQ/Q5XJncIwnYW5fJ4D6bNpEeZ2Y/NUn5GFLRVALvnVrdmH5TNXGdaLGnE6mLHLCB37wn2cPzXSA3XzsrXOILFm6sab9OmqBuarN/H98f8OdkU5jEWs0+kC0I1ecjW95Q09rfp3FFKP6KgoLzgsfQQLE5s= ddonggeunn@gmail.com",
            opts=pulumi.ResourceOptions(parent=self),
        )

        ubuntu = aws.ec2.get_ami(most_recent=True,
                                 filters=[
                                     aws.ec2.GetAmiFilterArgs(
                                         name="name",
                                         values=[
                                             "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-*-server-*"],
                                     ),
                                     aws.ec2.GetAmiFilterArgs(
                                         name="architecture",
                                         values=["arm64"]
                                     ),
                                     aws.ec2.GetAmiFilterArgs(
                                         name="virtualization-type",
                                         values=["hvm"],
                                     ),
                                 ],
                                 owners=["099720109477"])

        # /var/log/cloud-init-output.log
        user_data = f"""#!/bin/bash -ex
            echo BEGIN
            sudo su
            lsblk
            mkdir /data
            NAME=$(lsblk | grep 2T | awk '{{print $1}}')
            mount /dev/$NAME /data
            cp /etc/fstab /etc/fstab.orig
            BLOCK_UUID=$(lsblk -n /dev/$NAME -o UUID)
            if ! grep -q 'data' /etc/fstab; then
            bash -c "echo 'UUID=\"$BLOCK_UUID\"     /data       xfs    defaults,nofail   0   2' >> /etc/fstab";
            fi
            
            cd /home/ubuntu
            wget https://github.com/bnb-chain/bsc/releases/download/v1.4.6/geth-linux-arm64
            mv geth-linux-arm64 geth
            chmod -v u+x geth
            apt install unzip -y
            wget https://github.com/bnb-chain/bsc/releases/download/v1.4.6/mainnet.zip
            unzip mainnet.zip
            sed -i '/\[Node\.LogConfig\]/,$d' config.toml
            sed -i 's/PriceLimit = 3000000000/PriceLimit = 0/' config.toml
            nohup ./geth --config config.toml --datadir "/data" \
            --rpc.allow-unprotected-txs \
            --history.transactions 0 \
            --http.corsdomain "*" \
            --http \
            --http.addr 0.0.0.0 \
            --http.port 8545 \
            --http.corsdomain "*" \
            --http.api admin,db,debug,eth,net,personal,txpool,web3 \
            --http.vhosts "*" \
            --ws \
            --ws.addr 0.0.0.0 \
            --ws.port 8546 \
            --ws.origins "*" \
            --ws.api admin,db,debug,eth,net,personal,txpool,web3 \
            --gcmode full \
            --cache 16384 \
            --mainnet \
            --syncmode snap \
            --nat extip:$(hostname -i) \
            --db.engine=pebble \
            --maxpeers 100 \
            --state.scheme=path \
            &> /data/log.log &
            
            echo END
        """

        instance = aws.ec2.Instance(
            f"{name}-instance",
            instance_type="m7g.4xlarge",
            ami=ubuntu.id,
            key_name=key_pair.key_name,
            iam_instance_profile=instance_profile.name,
            tags={"Name": name},
            ebs_optimized=True,
            network_interfaces=[aws.ec2.InstanceNetworkInterfaceArgs(
                network_interface_id=network_interface.id,
                device_index=0,
            )],
            ebs_block_devices=[aws.ec2.InstanceEbsBlockDeviceArgs(
                device_name="/dev/sdf",
                volume_size=2048,
                iops=16000,
                throughput=1000,
                volume_type="gp3",
                snapshot_id=snapshot_id,
                tags={"Name": f"{name}-chain-data-volume"},
                delete_on_termination=True,
            )],
            root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
                volume_size=30,
                volume_type="gp3",
            ),
            user_data=user_data,
            opts=pulumi.ResourceOptions(parent=self,
                                        depends_on=[role, instance_profile, key_pair],
                                        delete_before_replace=True)
        )

        self.instances = [instance]
        self.register_outputs(
            {
                "instances": self.instances,
            }
        )


class NodeResource(pulumi.ComponentResource):
    def __init__(self, name, index, snapshot_id, first, opts=None):
        super().__init__("node", name, {}, opts)

        repository = ECR(f"{name}-ecr", opts=pulumi.ResourceOptions(parent=self))

        if not first:
            vpc = VPC(f"{name}-vpc", index, opts=pulumi.ResourceOptions(parent=self))
            DLM(f"{name}-dlm", opts=pulumi.ResourceOptions(parent=self))

            network_interface = NetworkInterface(f"{name}-network-interface", index,
                                                 vpc.subnet, vpc.security_group,
                                                 opts=pulumi.ResourceOptions(parent=self))

            ec2 = EC2(f"{name}-ec2", snapshot_id, network_interface.network_interface,
                      vpc.security_group,
                      opts=pulumi.ResourceOptions(parent=self))
