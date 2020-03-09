import os
import uuid
import json
import time
from pathlib import Path
from unittest import TestCase

import boto3

S3_SLEEP = 3


class PackageIntegBase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.region_name = os.environ.get("AWS_DEFAULT_REGION")
        """
        Our integration tests use S3 bucket to run several tests. Given that S3 objects are eventually consistent
        and we are using same bucket for lot of integration tests, we want to have multiple buckets to reduce
        transient failures. In order to achieve this we created 3 buckets one for each python version we support (3.6,
        3.7 and 3.8). Tests running for respective python version will use respective bucket.

        AWS_S3 will point to a new environment variable AWS_S3_36 or AWS_S3_37 or AWS_S3_38. This is controlled by
        Appveyor. These environment variables will hold bucket name to run integration tests. Eg:

        For Python36:
        AWS_S3=AWS_S3_36
        AWS_S3_36=aws-sam-cli-canary-region-awssamclitestbucket-forpython36

        For backwards compatibility we are falling back to reading AWS_S3 so that current tests keep working.
        """
        cls.pre_created_bucket = os.environ.get(os.environ.get("AWS_S3"), False)
        cls.bucket_name = cls.pre_created_bucket if cls.pre_created_bucket else str(uuid.uuid4())
        cls.test_data_path = Path(__file__).resolve().parents[1].joinpath("testdata", "package")

        # Intialize S3 client
        s3 = boto3.resource("s3")
        # Use a pre-created KMS Key
        cls.kms_key = os.environ.get("AWS_KMS_KEY")
        # Use a pre-created S3 Bucket if present else create a new one
        cls.s3_bucket = s3.Bucket(cls.bucket_name)
        if not cls.pre_created_bucket:
            cls.s3_bucket.create()
            time.sleep(S3_SLEEP)

    def setUp(self):
        super(PackageIntegBase, self).setUp()

    def tearDown(self):
        super(PackageIntegBase, self).tearDown()

    def base_command(self):
        command = "sam"
        if os.getenv("SAM_CLI_DEV"):
            command = "samdev"

        return command

    def get_command_list(
        self,
        s3_bucket=None,
        template=None,
        template_file=None,
        s3_prefix=None,
        output_template_file=None,
        use_json=False,
        force_upload=False,
        kms_key_id=None,
        metadata=None,
    ):
        command_list = [self.base_command(), "package"]

        if s3_bucket:
            command_list = command_list + ["--s3-bucket", str(s3_bucket)]
        if template:
            command_list = command_list + ["--template", str(template)]
        if template_file:
            command_list = command_list + ["--template-file", str(template_file)]

        if s3_prefix:
            command_list = command_list + ["--s3-prefix", str(s3_prefix)]

        if output_template_file:
            command_list = command_list + ["--output-template-file", str(output_template_file)]
        if kms_key_id:
            command_list = command_list + ["--kms-key-id", str(kms_key_id)]
        if use_json:
            command_list = command_list + ["--use-json"]
        if force_upload:
            command_list = command_list + ["--force-upload"]
        if metadata:
            command_list = command_list + ["--metadata", json.dumps(metadata)]

        return command_list
