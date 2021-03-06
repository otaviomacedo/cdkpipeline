from aws_cdk import core as cdk

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk.aws_codepipeline import StagePlacement
from aws_cdk.aws_codepipeline_actions import ManualApprovalAction
from aws_cdk.aws_iam import PolicyDocument
from aws_cdk.core import SecretValue, Environment, Stage, Stack
from aws_cdk.pipelines import CdkPipeline, SimpleSynthAction, ShellScriptAction, AdditionalArtifact

from aws_cdk import (core,
                     aws_codebuild as codebuild,
                     aws_codecommit as codecommit,
                     aws_iam as iam,
                     aws_s3 as s3,
                     aws_codepipeline as codepipeline,
                     aws_codepipeline_actions as codepipeline_actions,
                     )

from utils.configBuilder import WmpConfig
from workflow_cdk.stacks.cdk_argo_events_stack import CdkArgoEventsStack
from workflow_cdk.stacks.cdk_argo_workflows_stack import CdkArgoWorkflowsStack
from workflow_cdk.stacks.cdk_eks_stack import CdkEksStack
from workflow_cdk.stacks.cdk_kafka_stack import CdkKafkaStack
from workflow_cdk.stacks.cdk_manifests_stack import CdkManifestsStack
from workflow_cdk.stacks.cdk_vpc_stack import CdkVpcStack
from workflow_cdk.stages.cdk_application_stage import WmpApplicationStage


class WmpPipelineStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        source_artifact = codepipeline.Artifact()
        cloud_assembly_artifact = codepipeline.Artifact()
        #
        cpp = codepipeline.Pipeline(
            self,
            'Wmp-CodePipeline',
            pipeline_name='Wmp-Codepipeline',
            # artifact_bucket=s3.Bucket(self, 'artifact_bucket', encryption=s3.BucketEncryption.KMS),
            role=iam.Role(
                self,
                'Codepipeline-Role',
                assumed_by=iam.CompositePrincipal(
                    iam.ServicePrincipal('eks.amazonaws.com'),
                    iam.ServicePrincipal('s3.amazonaws.com'),
                    iam.ServicePrincipal('codepipeline.amazonaws.com')
                ),
                role_name='wmp-pipeline-role',
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name='AmazonS3FullAccess')
                ]
            )
        )

        #
        sourceStage = cpp.add_stage(stage_name='Source', actions=[
            codepipeline_actions.GitHubSourceAction(
                action_name="GitHub_SourceCode_Download",
                output=source_artifact,
                oauth_token=SecretValue.secrets_manager('triage'),
                trigger=codepipeline_actions.GitHubTrigger.POLL,
                owner="otaviomacedo",
                repo="cdkpipeline",
                branch='main'
            )
        ])
        #
        buildStage = cpp.add_stage(
            stage_name='Build',
            actions=[
                SimpleSynthAction(
                    synth_command='cdk synth',
                    cloud_assembly_artifact=cloud_assembly_artifact,
                    source_artifact=source_artifact,
                    install_commands=[
                        "npm install -g aws-cdk",
                        "pip install -r requirements.txt",
                        "python setup.py install"
                    ]
                )
            ],
            placement=StagePlacement(just_after=sourceStage)
        )

        # teststage = cpp.add_stage(
        #     stage_name='Deploy',
        #     actions=[
        #         codepipeline_actions.CloudFormationCreateUpdateStackAction(
        #             action_name='Deploy',
        #             admin_permissions=True,
        #             stack_name='DeployStack',
        #             template_path=codepipeline.ArtifactPath(source_artifact, file_name='template.yaml'),
        #             run_order=1
        #         ),
        #         codepipeline_actions.ManualApprovalAction(action_name='ApproveChanges', run_order=2),
        #         codepipeline_actions.CloudFormationExecuteChangeSetAction(
        #             action_name='ExecuteChanges',
        #             stack_name='DeployStack',
        #             change_set_name='StagedChangeSet',
        #             run_order=3
        #         )
        #     ]
        # )
        #

        pipeline = CdkPipeline(
            self, "Wmp-CdkPipeline1",
            cloud_assembly_artifact=cloud_assembly_artifact,
            code_pipeline=cpp,
            self_mutating=False
        )
        #
        # pipeline = CdkPipeline(
        #     self, "Pipeline",
        #     pipeline_name="Wmp-Codepipeline",
        #     cloud_assembly_artifact=cloud_assembly_artifact,
        #     source_action=codepipeline_actions.GitHubSourceAction(
        #         action_name="GitHub_SourceCode_Download",
        #         output=source_artifact,
        #         oauth_token=SecretValue.plain_text('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'),
        #         trigger=codepipeline_actions.GitHubTrigger.POLL,
        #         owner="uxth",
        #         repo="cdkpipeline",
        #         branch='main'
        #     ),
        #     synth_action=SimpleSynthAction(
        #         synth_command='cdk synth',
        #         cloud_assembly_artifact=cloud_assembly_artifact,
        #         source_artifact=source_artifact,
        #         install_commands=[
        #             "npm install -g aws-cdk",
        #             "pip install -r requirements.txt",
        #             "python setup.py install",
        #             'cdk synth'
        #         ]
        #     ),
        #     self_mutating=False
        # )

        #
        # buildRole = iam.Role(self, 'buildRole', assumed_by=iam.ServicePrincipal('codebuild.amazonaws.com'))
        # buildStage = pipeline.add_stage('appBuild')
        # buildSpec = codebuild.BuildSpec.from_object(
        #     {
        #         'version': '0.2',
        #         'env': {
        #             'compute-type': 'build.general1.small',
        #             'image': 'aws/codebuild/amazonlinux2-x86_64-standard:2.0'
        #         },
        #         'phases': {
        #             'install': {
        #               'runtime-versions': {
        #                   'python': 3.7
        #               }
        #             },
        #             'pre_build': {
        #                 'commands': [
        #                     'pip install -r requirements.txt',
        #                     'pip install -e .',
        #                 ]
        #             }
        #         },
        #     }
        # )
        # buildStage.add_actions(
        #     codepipeline_actions.CodeBuildAction(
        #         action_name='Build',
        #         input=source_artifact,
        #         project=codebuild.Project(
        #             self,
        #             'Build',
        #             role=buildRole,
        #             environment=codebuild.BuildEnvironment(
        #                 build_image=codebuild.LinuxBuildImage.STANDARD_4_0,
        #                 privileged=True
        #             ),
        #             build_spec=buildSpec
        #         )
        #     )
        # )

        teststage = pipeline.add_application_stage(
            WmpApplicationStage(
                self,
                'alpha-stage',
                config=WmpConfig('workflow_cdk/config/config.json', 'test')
            ),
            manual_approvals=False
        )
