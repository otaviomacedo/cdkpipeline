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


class CdkDeployStack(Stack):
    def __init__(self, scope: Construct, id: str, config: WmpConfig, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        vpc = ec2.Vpc(
            self,
            "wmp-vpc",
            cidr=config.getValue('vpc.cidr')
        )
        eks_uer = iam.User(
            self, id="wmp-eks-user",
            user_name=config.getValue('eks.admin_username'),
            password=core.SecretValue.plain_text(config.getValue('eks.admin_password'))  # this needs to be put in KMS
        )
        policy = iam.Policy(
            self, id='wmp-eks-policy',
            policy_name='EKSFullAccessPolicy',
            statements=[
                iam.PolicyStatement(
                    sid='EKSFullAccess',
                    effect=iam.Effect.ALLOW,
                    actions=['eks:*'],
                    resources=['*']
                )
            ],
            users=[eks_uer]
        )

        eks_role = iam.Role(
            self, id="wmp-eks-admin",
            # assumed_by=iam.ArnPrincipal(arn=eks_uer.user_arn),
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('eks.amazonaws.com'),
                iam.ServicePrincipal('s3.amazonaws.com'),
                iam.ArnPrincipal(arn=eks_uer.user_arn)
            ),
            role_name='wmp-eks-cluster-role',
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name="AdministratorAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name='AmazonS3FullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name='AmazonEKSClusterPolicy'),
            ],
            inline_policies={
                'KMSFullAccess': PolicyDocument(
                    assign_sids=True,
                    statements=[
                        iam.PolicyStatement(
                            sid='KMSFullAccess',
                            effect=iam.Effect.ALLOW,
                            actions=['kms:*'],
                            resources=['*']
                        )
                    ]
                )
            }
        )

        self.cluster = eks.Cluster(
            self, id='wmp-eks-cluster',
            cluster_name=config.getValue('eks.cluster_name'),
            version=eks.KubernetesVersion.V1_19,
            vpc=vpc,
            vpc_subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE)],
            default_capacity=0,
            masters_role=eks_role
        )

        self.cluster.add_nodegroup_capacity(
            'wmp-eks-nodegroup',
            instance_types=[ec2.InstanceType(config.getValue('eks.nodegroup.instance_type'))],
            disk_size=config.getValue('eks.nodegroup.disk_size'),
            min_size=config.getValue('eks.nodegroup.min_size'),
            max_size=config.getValue('eks.nodegroup.max_size'),
            desired_size=config.getValue('eks.nodegroup.desired_size'),
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),
            capacity_type=eks.CapacityType.SPOT
        )


class WmpApplicationStage(Stage):
    def __init__(self, scope: Construct, id: str, config: WmpConfig, **kwargs):
        super().__init__(scope, id, **kwargs)
        env = Environment(
            account=config.getValue('AWSAccountID'),
            region=config.getValue('AWSProfileRegion')
        )
        # vpc_stack = CdkVpcStack(
        #     self, "wmp-vpc",
        #     config=config,
        #     env=env)
        #
        # eks_stack = CdkEksStack(
        #     self, 'wmp-eks',
        #     vpc=vpc_stack.vpc,
        #     config=config,
        #     env=env)
        # eks_stack.add_dependency(vpc_stack)
        #
        # kafka_stack = CdkKafkaStack(
        #     self, 'wmp-kafka',
        #     eks_stack=eks_stack,
        #     config=config,
        #     env=env)
        # kafka_stack.add_dependency(eks_stack)
        #
        # argo_workflows_stack = CdkArgoWorkflowsStack(
        #     self, 'wmp-argo-workflows',
        #     eks_stack=eks_stack,
        #     config=config,
        #     env=env)
        # argo_workflows_stack.add_dependency(eks_stack)
        #
        # argo_events_stack = CdkArgoEventsStack(
        #     self, 'wmp-argo-events',
        #     eks_stack=eks_stack,
        #     config=config,
        #     env=env)
        # argo_events_stack.add_dependency(argo_workflows_stack)
        # argo_events_stack.add_dependency(kafka_stack)
        #
        # manifests_stack = CdkManifestsStack(
        #     self, 'wmp-manifests',
        #     eks_stack=eks_stack,
        #     config=config,
        #     env=env)
        # manifests_stack.add_dependency(argo_events_stack)
        CdkDeployStack(
            self,
            'DeployStack',
            config=config,
            env=env
        )
