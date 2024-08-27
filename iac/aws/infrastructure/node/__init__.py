import pulumi
from .resource import NodeResource


class Nodes(pulumi.ComponentResource):
    def __init__(self, name: str, opts: pulumi.ResourceOptions = None):
        super().__init__("nodes", name, None, opts)

        self.nodes = [
            NodeResource("node-bsc", 1, "snap-0f09e15b17e905e18", first=False)
        ]
