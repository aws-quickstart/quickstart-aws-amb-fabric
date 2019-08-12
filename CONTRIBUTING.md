# Contributing

## Setting up your dev environment
1. Install [taskcat](https://github.com/aws-quickstart/taskcat):
  `pip3 install taskcat`
2. Set up AWS CLI
  `pip3 install awscli`
3. Make sure you put your IAM user's credentials into `~/.aws/credentials`
4. `git submodule update --init --recursive`

## Testing your changes
1. `scripts/test.sh`
2. Open the AWS console to track your CloudFormation stacks as they are created.

This installation uses the Control Center pattern because Amazon Managed Blockchain doesn't yet support CloudFormation. It launches an EC2 instance from which the AMB setup takes place using the AWS CLI. To troubleshoot errors on the Control Center instance:
1. Go to EC2 in your AWS Console
2. Select Instances
3. Look for an instance called seednodeX. Click on it.
4. Refresh until you see a value for public DNS. Copy that to your clipboard.
5. SSH to that instance by pasting the public DNS endpoint in the appropriate spot:
    `ssh ubuntu@ec2-X-X-X-X.compute-X.amazonaws.com`
6. `cd /var/log`
7. Look in `cfn-init.log` and other adjacent log files for logs of script activity.
8. You can also make your CloudFormation template write files to `/tmp` to sanity-check certain values. For example:
    ```
    commands:
        01_post_run_command:
            command: echo $MYVAR > /tmp/somevar.txt
    ```
The templates take quite a while to execute. Be patient ;-). Also, if you're done testing something, you can delete the root CloudFormation stack before it's finished, make modifications, and run the test script again.

Be aware that because we're using the Control Center pattern, you will need to delete AMB networks in the Console, as they will not be dismantled along with your CloudFormation stack.