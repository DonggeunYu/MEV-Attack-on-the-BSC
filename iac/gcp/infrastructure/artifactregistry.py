import pulumi
import pulumi_gcp as gcp

config = pulumi.Config("gcp")
project = config.require("project")
region = config.require("region")
zone = config.require("zone")

docker_registry = gcp.artifactregistry.Repository(
    "docker-registry",
    format="DOCKER",
    location=region,
    project=project,
    repository_id="docker-registry",
)
