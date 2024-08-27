import pulumi
import pulumi_gcp as gcp

# Import the program's configuration settings.
config = pulumi.Config("gcp")
project = config.require("project")

cloudresourcemanager_googleapis = gcp.projects.Service(
    "cloudresourcemanager-googleapis",
    disable_dependent_services=True,
    project=project,
    service="cloudresourcemanager.googleapis.com",
)
pulumi.export("cloudresourcemanager_googleapis", cloudresourcemanager_googleapis)

iam_googleapis = gcp.projects.Service(
    "iam-googleapis",
    disable_dependent_services=True,
    project=project,
    service="iam.googleapis.com",
)
pulumi.export("iam_googleapis", iam_googleapis)

compute_googleapis = gcp.projects.Service(
    "compute-googleapis",
    disable_dependent_services=True,
    project=project,
    service="compute.googleapis.com",
)
pulumi.export("compute_googleapis", compute_googleapis)

artifactregistry_googleapis = gcp.projects.Service(
    "artifactregistry-googleapis",
    disable_dependent_services=True,
    project=project,
    service="artifactregistry.googleapis.com",
)
pulumi.export("artifactregistry_googleapis", artifactregistry_googleapis)
