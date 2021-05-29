from aws_cdk import (
    core,
    aws_eks as eks
)

from utils.configBuilder import WmpConfig
from workflow_cdk.stacks.cdk_eks_stack import CdkEksStack
from utils import yamlParser


class CdkArgoWorkflowsStack(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, eks_stack: CdkEksStack, config: WmpConfig, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # install argo workflows
        eks.KubernetesManifest(
            self, id='manifest',
            cluster=eks_stack.cluster,
            manifest=yamlParser.readManifest(paths=config.getValue('argo-workflow.manifests')))

        eks.HelmChart(
            self, id='wmp-argo-workflows', cluster=eks_stack.cluster, chart='argo-workflows',
            repository='https://argoproj.github.io/argo-helm',
            namespace='argo', release=config.getValue('argo-workflow.release'),
            values=yamlParser.readYaml(path=config.getValue('argo-workflow.valuesPath')),
            wait=True)
