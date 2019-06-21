#!/usr/bin/env python

import sys, os, subprocess, ast, argparse, random, time

parser = argparse.ArgumentParser(description='Set up Amazon Managed Blockchain')
parser.add_argument('--name', default='ACME')
parser.add_argument('--framework', default='HYPERLEDGER_FABRIC')
parser.add_argument('--framework-version', default='1.2')
parser.add_argument('--framework-configuration', default='STANDARD')
parser.add_argument('--admin-username', default='acmeadmin')
parser.add_argument('--admin-password', default='Admin123')
parser.add_argument('--threshold-percentage', type=int, default=50)
parser.add_argument('--proposal-duration', type=int, default=24)
parser.add_argument('--threshold-comparator', default='GREATER_THAN')
parser.add_argument('--node-count', type=int, default=2, help='3 max')
parser.add_argument('--node-type', default='bc.t3.small')
args = parser.parse_args()

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