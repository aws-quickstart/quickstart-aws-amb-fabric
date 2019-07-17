#!/usr/bin/env python

import subprocess, ast, argparse, random, time, re


def password_arg(value):
    if len(value) < 8:
        raise argparse.ArgumentTypeError('password must be at least 8 chars')
    if len(value) > 32:
        raise argparse.ArgumentTypeError('password cannot exceed 32 chars')
    forbidden = re.compile("[/\\\"'@ ]")
    if forbidden.search(value):
        raise argparse.ArgumentTypeError('password cannot contain \', ", \\, /, @ or spaces')
    required1 = re.compile("[A-Z]")
    if not required1.search(value):
        raise argparse.ArgumentTypeError('password must have at least one uppercase char')
    required2 = re.compile("[a-z]")
    if not required2.search(value):
        raise argparse.ArgumentTypeError('password must have at least one lowercase char')
    required3 = re.compile("[0-9]")
    if not required3.search(value):
        raise argparse.ArgumentTypeError('password must have at least one digit')
    return value


def framework_arg(value):
    if value != 'HYPERLEDGER_FABRIC':
        raise argparse.ArgumentTypeError('framework must be HYPERLEDGER_FABRIC')
    return value


def name_arg(value):
    pattern = re.compile('^[A-Za-z0-9]+$')
    if not pattern.match(value):
        raise argparse.ArgumentTypeError('name can only contain alphanumeric characters')
    return value


def framework_version_arg(value):
    if value != '1.2':
        raise argparse.ArgumentTypeError('framework version must be 1.2')
    return value


def framework_configuration_arg(value):
    if value != 'STARTER' and value != 'STANDARD':
        raise argparse.ArgumentTypeError('framework configuration must be STARTER or STANDARD')
    return value


def username_arg(value):
    pattern = re.compile('^[a-z][a-z0-9]{2,16}$')
    if not pattern.match(value):
        raise argparse.ArgumentTypeError('admin username must begin with a letter and be alphanumeric')
    if len(value) < 3:
        raise argparse.ArgumentTypeError('admin username must be at least three characters long')
    return value


def threshold_percentage_arg(value):
    if value < 1 or value > 100:
        raise argparse.ArgumentTypeError('threshold percentage must be an integer between 1 and 100')
    return value


def proposal_duration_arg(value):
    if value < 1 or value > 168:
        raise argparse.ArgumentTypeError('proposal duration must be an integer between 1 and 168')
    return value


def threshold_comparator_arg(value):
    if value != 'GREATER_THAN' and value != 'GREATER_THAN_OR_EQUAL_TO':
        raise argparse.ArgumentTypeError('threshold comparator must be GREATER_THAN or GREATER_THAN_OR_EQUAL_TO')
    return value


parser = argparse.ArgumentParser(description='Set up Amazon Managed Blockchain')
parser.add_argument('--name', default='ACME', required=True, type=name_arg)
parser.add_argument('--framework', default='HYPERLEDGER_FABRIC', type=framework_arg)
parser.add_argument('--framework-version', default='1.2', type=framework_version_arg)
parser.add_argument('--framework-configuration', default='STANDARD', type=framework_configuration_arg)
parser.add_argument('--admin-username', default='acmeadmin', required=True, type=username_arg)
parser.add_argument('--admin-password', default='Admin123', required=True, type=password_arg)
parser.add_argument('--threshold-percentage', default=50, type=threshold_percentage_arg)
parser.add_argument('--proposal-duration', default=24, type=proposal_duration_arg)
parser.add_argument('--threshold-comparator', default='GREATER_THAN', type=threshold_comparator_arg)
parser.add_argument('--node-count', type=int, default=2, help='3 max')
parser.add_argument('--node-type', default='bc.t3.small')
args = parser.parse_args()

if args.framework_configuration == 'STARTER':
    if args.node_count > 2:
        raise argparse.ArgumentTypeError('node count cannot exceed 2 when framework configuration is STARTER')
    if args.node_type != 'bc.t3.small' and args.node_type != 'bc.t3.medium':
        raise argparse.ArgumentTypeError('node type must be bc.t3.small or bc.t3.medium when framework configuration is STARTER')

if args.node_count < 1 or args.node_count > 3:
    raise argparse.ArgumentTypeError('node count must be between 1 and 3')

pattern = re.compile('^bc\.(t3|m5|c5)\.(small|medium|x?large)$')
if not pattern.match(args.node_type):
    types = [
        'bc.t3.small',
        'bc.t3.medium',
        'bc.t3.large',
        'bc.t3.xlarge',
        'bc.m5.large',
        'bc.m5.xlarge',
        'bc.m5.2xlarge',
        'bc.m5.4xlarge',
        'bc.c5.large',
        'bc.c5.xlarge',
        'bc.c5.2xlarge',
        'bc.c5.4xlarge'
    ]
    raise argparse.ArgumentTypeError("node type must be one of {}".format(', '.join(types)))


member_options = {
    'name': args.name,
    'admin-username': args.admin_username,
    'admin-password': args.admin_password
}

voting_policy = {
    'threshold-percentage': args.threshold_percentage,
    'proposal-duration': args.proposal_duration,
    'threshold-comparator': args.threshold_comparator
}

chain_options = {
    'name': args.name,
    'framework': args.framework,
    'framework-version': args.framework_version,
    'framework-configuration': 'Fabric={{Edition={0}}}'.format(args.framework_configuration),
    'member-configuration': "Name={name},FrameworkConfiguration={{"
                            "Fabric={{"
                            "AdminUsername={admin-username},"
                            "AdminPassword={admin-password}}}}}".format(**member_options),
    'voting-policy': "ApprovalThresholdPolicy={{"
                     "ThresholdPercentage={threshold-percentage},"
                     "ProposalDurationInHours={proposal-duration},"
                     "ThresholdComparator={threshold-comparator}}}".format(**voting_policy)
}

cmd = 'aws managedblockchain create-network'
for k, v in chain_options.items():
    cmd += ' --{0} "{1}"'.format(k, v)

print(cmd)

# create network
result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
output = result.stdout
print(output)
results = ast.literal_eval(output)

# wait for network to be created
status = 'CREATING'
while status == 'CREATING':
    cmd = 'aws managedblockchain list-networks'
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    output = result.stdout
    network_list = ast.literal_eval(output)
    for network in network_list['Networks']:
        if network['Id'] == results['NetworkId']:
            status = network['Status']
    print("Waiting for network to be created...")
    time.sleep(60)

print("Network status is {}".format(status))

if status == 'AVAILABLE':
    # create nodes
    zones = ['us-east-1a', 'us-east-1b', 'us-east-1c', 'us-east-1d', 'us-east-1e', 'us-east-1f']
    random.shuffle(zones)
    for i in range(args.node_count):
        node = {
            'network-id': results['NetworkId'],
            'member-id': results['MemberId'],
            'node-configuration':
                "InstanceType={0},"
                "AvailabilityZone={1}".format(args.node_type, zones.pop())
        }
        cmd = 'aws managedblockchain create-node'
        for k, v in node.items():
            cmd += ' --{0} "{1}"'.format(k, v)
        print(cmd)
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True)
        output = result.stdout
        print(output)
else:
    print("Network wasn't created properly. Please delete the network in the AWS console and try again.")