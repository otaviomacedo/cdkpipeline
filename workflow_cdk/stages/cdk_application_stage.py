from aws_cdk.aws_iam import PolicyDocument
from aws_cdk.core import Construct, Stack, Stage, Environment
from aws_cdk import (
    aws_ec2 as ec2,
    core,
    aws_iam as iam,
    aws_eks as eks
)
from aws_cdk.pipelines import CdkPipeline
import aws_cdk.aws_codepipeline as code_pipeline

from utils.configBuilder import WmpConfig
from workflow_cdk.stacks.cdk_argo_events_stack import CdkArgoEventsStack
from workflow_cdk.stacks.cdk_argo_workflows_stack import CdkArgoWorkflowsStack
from workflow_cdk.stacks.cdk_eks_stack import CdkEksStack
from workflow_cdk.stacks.cdk_kafka_stack import CdkKafkaStack
from workflow_cdk.stacks.cdk_manifests_stack import CdkManifestsStack
from workflow_cdk.stacks.cdk_vpc_stack import CdkVpcStack


class WmpApplicationStage(Stage):
    def __init__(self, scope: Construct, id: str, config: WmpConfig, **kwargs):
        super().__init__(scope, id, **kwargs)
        env = Environment(
            account=config.getValue('AWSAccountID'),
            region=config.getValue('AWSProfileRegion')
        )
        vpc_stack = CdkVpcStack(
            self, "wmp-vpc",
            config=config,
            env=env)

        eks_stack = CdkEksStack(
            self, 'wmp-eks',
            vpc=vpc_stack.vpc,
            config=config,
            env=env)
        eks_stack.add_dependency(vpc_stack)

        kafka_stack = CdkKafkaStack(
            self, 'wmp-kafka',
            eks_stack=eks_stack,
            config=config,
            env=env)
        kafka_stack.add_dependency(eks_stack)

        argo_workflows_stack = CdkArgoWorkflowsStack(
            self, 'wmp-argo-workflows',
            eks_stack=eks_stack,
            config=config,
            env=env)
        argo_workflows_stack.add_dependency(eks_stack)

        argo_events_stack = CdkArgoEventsStack(
            self, 'wmp-argo-events',
            eks_stack=eks_stack,
            config=config,
            env=env)
        argo_events_stack.add_dependency(argo_workflows_stack)
        argo_events_stack.add_dependency(kafka_stack)

        manifests_stack = CdkManifestsStack(
            self, 'wmp-manifests',
            eks_stack=eks_stack,
            config=config,
            env=env)
        manifests_stack.add_dependency(argo_events_stack)
