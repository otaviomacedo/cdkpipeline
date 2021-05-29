from aws_cdk import (core,
                     aws_codebuild as codebuild,
                     aws_codecommit as codecommit,
                     aws_iam as iam,
                     aws_codepipeline as codepipeline,
                     aws_codepipeline_actions as codepipeline_actions,
                     pipelines)

from workflow_cdk.stages.cdk_application_stage import WmpApplicationStage


class CdkPipelineStack(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # source_artifact = codepipeline.Artifact()
        #
        # buildSpec = codebuild.BuildSpec.from_object(
        #     {
        #         'version': '0.2',
        #         'phases': {
        #             'pre_build': {
        #                 'commands': [
        #                     'echo Logging in to Amazon ECR...',
        #                     '$(aws ecr get-login --no-include-email --region $AWS_DEFAULT_REGION)',
        #                 ]
        #             },
        #             'build': {
        #                 'commands': [
        #                     'echo Build started on `date`',
        #                     'echo Building the Docker image...',
        #                     '`docker build -t ${repositoryUri}:$CODEBUILD_RESOLVED_SOURCE_VERSION .`',
        #                 ]
        #             },
        #             'post_build': {
        #                 'commands': [
        #                     'echo Build completed on `date`',
        #                     'echo Pushing the Docker image...',
        #                     '`docker push ${repositoryUri}:$CODEBUILD_RESOLVED_SOURCE_VERSION`',
        #                 ]
        #             },
        #         },
        #     }
        # )
        # buildRole = iam.Role(self, 'buildRole', assumed_by=iam.ServicePrincipal('codebuild.amazonaws.com'))
        #
        # codePipeline = codepipeline.Pipeline(self, 'codepipeline', stages=[
        #     codepipeline.StageProps(stage_name='Source', actions=[
        #         codepipeline_actions.GitHubSourceAction(
        #             oauth_token=core.SecretValue.plain_text('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'),
        #             output=source_artifact,
        #             owner='uxth',
        #             repo='cdkpipeline',
        #             action_name='download_source',
        #             branch='main',
        #             trigger=codepipeline_actions.GitHubTrigger.POLL
        #         )
        #     ]),
        #     codepipeline.StageProps(stage_name='build', actions=[
        #         codepipeline_actions.CodeBuildAction(
        #             action_name='build',
        #             input=source_artifact,
        #             project=codebuild.Project(
        #                 self,
        #                 'cdk_pipeline_project',
        #                 role=buildRole,
        #                 environment=codebuild.BuildEnvironment(
        #                     build_image=codebuild.LinuxBuildImage.STANDARD_4_0,
        #                     privileged=True
        #                 ),
        #                 build_spec=buildSpec
        #             ),
        #             role=buildRole,
        #             outputs=[codepipeline.Artifact()]
        #         )
        #     ])
        # ])
        #
######


        source_artifact = codepipeline.Artifact()
        cloud_assembly_artifact = codepipeline.Artifact()
        cdkPipeline = pipelines.CdkPipeline(
            self,
            id='wmp_pipeline',
            pipeline_name='wmp_pipeline',
            cloud_assembly_artifact=cloud_assembly_artifact,
            source_action=codepipeline_actions.GitHubSourceAction(
                    oauth_token=core.SecretValue.plain_text('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'),
                    output=source_artifact,
                    owner='uxth',
                    repo='cdkpipeline',
                    action_name='download_source',
                    branch='main',
                    trigger=codepipeline_actions.GitHubTrigger.POLL
                ),
            synth_action=pipelines.SimpleSynthAction.standard_npm_synth(
                source_artifact=source_artifact,
                cloud_assembly_artifact=cloud_assembly_artifact,
            )
        )

        buildRole = iam.Role(self, 'buildRole', assumed_by=iam.ServicePrincipal('codebuild.amazonaws.com'))
        buildStage = cdkPipeline.add_stage('appBuild')
        buildSpec = codebuild.BuildSpec.from_object(
            {
                'version': '0.2',
                'phases': {
                    'pre_build': {
                        'commands': [
                            'echo Logging in to Amazon ECR...',
                            '$(aws ecr get-login --no-include-email --region $AWS_DEFAULT_REGION)',
                        ]
                    },
                    'build': {
                        'commands': [
                            'echo Build started on `date`',
                            'echo Building the Docker image...',
                            '`docker build -t ${repositoryUri}:$CODEBUILD_RESOLVED_SOURCE_VERSION .`',
                        ]
                    },
                    'post_build': {
                        'commands': [
                            'echo Build completed on `date`',
                            'echo Pushing the Docker image...',
                            '`docker push ${repositoryUri}:$CODEBUILD_RESOLVED_SOURCE_VERSION`',
                        ]
                    },
                },
            }
        )
        buildStage.add_actions(
            codepipeline_actions.CodeBuildAction(
                action_name='Build',
                input=source_artifact,
                project=codebuild.Project(
                    self,
                    'Build',
                    role=buildRole,
                    environment=codebuild.BuildEnvironment(
                        build_image=codebuild.LinuxBuildImage.STANDARD_4_0,
                        privileged=True
                    ),
                    build_spec=buildSpec
                )
            )
        )
        #
        applicationStage = WmpApplicationStage(scope, 'dev')
        cdkPipeline.add_application_stage(applicationStage)

