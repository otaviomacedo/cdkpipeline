#!/usr/bin/env python3

# For consistency with TypeScript code, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.


from aws_cdk import core
from utils.configBuilder import WmpConfig


from workflow_cdk.stacks.cdk_argo_events_stack import CdkArgoEventsStack
from workflow_cdk.stacks.cdk_argo_workflows_stack import CdkArgoWorkflowsStack
from workflow_cdk.stacks.cdk_manifests_stack import CdkManifestsStack
from workflow_cdk.stacks.cdk_pipeline_stack import CdkPipelineStack
from workflow_cdk.stacks.cdk_vpc_stack import CdkVpcStack
from workflow_cdk.stacks.cdk_eks_stack import CdkEksStack
from workflow_cdk.stacks.cdk_kafka_stack import CdkKafkaStack

app = core.App()

config = WmpConfig('workflow_cdk/config/config.json', app.node.try_get_context('config'))
env = core.Environment(
    account=config.getValue('AWSAccountID'),
    region=config.getValue('AWSProfileRegion')
)
vpc_stack = CdkVpcStack(
    app, "wmp-vpc",
    config=config,
    env=env)

eks_stack = CdkEksStack(
    app, 'wmp-eks',
    vpc=vpc_stack.vpc,
    config=config,
    env=env)
eks_stack.add_dependency(vpc_stack)

kafka_stack = CdkKafkaStack(
    app, 'wmp-kafka',
    eks_stack=eks_stack,
    config=config,
    env=env)
kafka_stack.add_dependency(eks_stack)

argo_workflows_stack = CdkArgoWorkflowsStack(
    app, 'wmp-argo-workflows',
    eks_stack=eks_stack,
    config=config,
    env=env)
argo_workflows_stack.add_dependency(eks_stack)

argo_events_stack = CdkArgoEventsStack(
    app, 'wmp-argo-events',
    eks_stack=eks_stack,
    config=config,
    env=env)
argo_events_stack.add_dependency(argo_workflows_stack)
argo_events_stack.add_dependency(kafka_stack)

manifests_stack = CdkManifestsStack(
    app, 'wmp-manifests',
    eks_stack=eks_stack,
    config=config,
    env=env)
manifests_stack.add_dependency(argo_events_stack)

# CdkPipelineStack(app, 'wmp-pipeline')
app.synth()
