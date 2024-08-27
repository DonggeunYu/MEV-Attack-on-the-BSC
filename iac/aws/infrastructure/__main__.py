import pulumi
import pulumi_aws as aws
import pulumi_aws_native as aws_native
from node import Nodes

aws_config = pulumi.Config("aws")
aws.Provider(
    resource_name="provider",
    region=aws_config.require("region"),
    access_key=aws_config.require("accessKey"),
    secret_key=aws_config.require("secretKey"),
)

aws_native_config = pulumi.Config("aws-native")
aws_native.Provider(
    resource_name="native",
    region=aws_native_config.require("region"),
    access_key=aws_native_config.require("accessKey"),
    secret_key=aws_native_config.require("secretKey"),
)

node = Nodes("nodes")
