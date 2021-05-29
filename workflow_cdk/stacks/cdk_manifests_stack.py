from aws_cdk import (
    core,
    aws_eks as eks
)

from utils.configBuilder import WmpConfig
from workflow_cdk.stacks.cdk_eks_stack import CdkEksStack
from utils import yamlParser

class CdkManifestsStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, eks_stack: CdkEksStack, config: WmpConfig, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        eks.KubernetesManifest(
            self,
            id='wmp-manifest',
            cluster=eks_stack.cluster,
            manifest=yamlParser.readManifest(
                paths=config.getValue('manifests.files')
            )
        )

