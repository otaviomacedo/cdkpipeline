from aws_cdk import (
    core,
    aws_eks as eks,
    aws_ec2 as ec2,
    aws_iam as iam
)

from utils.configBuilder import WmpConfig


class CdkEksStack(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, vpc: ec2.Vpc, config: WmpConfig, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        eks_uer = iam.User(
            self, id="wmp-eks-user",
            user_name=config.getValue('eks.admin_username'),
            password=core.SecretValue.plain_text(config.getValue('eks.admin_password'))  # this needs to be put in KMS
        )
        iam.Policy(
            self, id='wmp-eks-policy',
            policy_name='EKSFullAccessPolicy',
            statements=[
                iam.PolicyStatement(
                    sid='EKSFullAccess',
                    effect=iam.Effect.ALLOW,
                    actions=['*'],
                    resources=['*']
                )
            ],
            users=[eks_uer]
        )

        eks_role = iam.Role(
            self, id="wmp-eks-admin",
            assumed_by=iam.ArnPrincipal(arn=eks_uer.user_arn),
            role_name='wmp-eks-cluster-role',
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name="AdministratorAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name='AmazonS3FullAccess')
            ]
        )
        self.cluster = eks.Cluster(
            self, id='wmp-eks-cluster',
            # cluster_name=config.getValue('eks.cluster_name'),
            cluster_name='eks-cluster',
            version=eks.KubernetesVersion.V1_19,
            vpc=vpc,
            vpc_subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE)],
            default_capacity=0,
            masters_role=eks_role,
            role=eks_role
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
