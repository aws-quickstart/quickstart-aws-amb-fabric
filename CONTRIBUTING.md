# Contributing

## Setting up your dev environment
1. Install [taskcat](https://github.com/aws-quickstart/taskcat):
  `pip3 install taskcat`
2. Set up AWS CLI
  `pip3 install awscli`
3. Make sure you put your IAM user's credentials into `~/.aws/credentials`
4. `git submodule update --init --recursive`

## Testing your changes
`taskcat -c ci/taskcat.yml`
