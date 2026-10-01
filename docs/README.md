# Documentation

Start with [Getting started](getting-started.md) for installation, profiles, invocation forms, and output handling. [Maintenance and recovery](maintenance.md) covers bootstrap, upgrades, updates, and backups.

## Guides

- [Profiles, identity, and IAM](identity.md)
- [EC2 instances, EBS, and AMIs](compute.md)
- [Regions and network inventory](network.md)
- [Security-group inspection and host rules](security-groups.md)
- [Logs, registries, and CSV reports](reports.md)
- [Local JSON and public-IP utilities](utilities.md)
- [Service shortcuts](service-shortcuts.md)
- [Retired compatibility commands](retired.md)
- [Troubleshooting](troubleshooting.md)

## Every alias

The inventory has 75 entries, including 13 retired compatibility names. Each command below links to its purpose, usage, and output contract. All examples use synthetic data.

| Alias | Purpose | Kind |
| --- | --- | --- |
| [ag](service-shortcuts.md#ag) | Use apigateway operations through a short service name. | Service shortcut |
| [allow-my-ip](security-groups.md#allow-my-ip) | Add one ingress rule for a single IPv4 or IPv6 host. | Helper |
| [allow-my-ip-all](retired.md#allow-my-ip-all) | Use allow-my-ip with an explicit group ID, protocol and port. | Retired |
| [amazon-linux-amis](compute.md#amazon-linux-amis) | Resolve the current Amazon Linux 2023 AMI ID for a region. | Helper |
| [ami-snapshots](compute.md#ami-snapshots) | List EBS snapshot IDs referenced by an AMI. | Helper |
| [as](service-shortcuts.md#as) | Use autoscaling operations through a short service name. | Service shortcut |
| [assume](retired.md#assume) | Configure a role profile and select it with --profile. | Retired |
| [authorize-my-ip-by-name](retired.md#authorize-my-ip-by-name) | Use allow-my-ip with an explicit group ID, protocol and port. | Retired |
| [cfn](service-shortcuts.md#cfn) | Use cloudformation operations through a short service name. | Service shortcut |
| [cp](service-shortcuts.md#cp) | Use codepipeline operations through a short service name. | Service shortcut |
| [create-assume-role](retired.md#create-assume-role) | Define the role and trust policy in reviewed infrastructure code. | Retired |
| [ddb](service-shortcuts.md#ddb) | Use dynamodb operations through a short service name. | Service shortcut |
| [delete-ami](retired.md#delete-ami) | Use ami-snapshots <ami-id> to list the associated snapshots. | Retired |
| [delete-virtual-mfa](retired.md#delete-virtual-mfa) | Use an administrator MFA deactivation/deletion procedure. | Retired |
| [docker-ecr-login](reports.md#docker-ecr-login) | Authenticate the local Docker client to a private ECR registry. | Helper |
| [eb](service-shortcuts.md#eb) | Use elasticbeanstalk operations through a short service name. | Service shortcut |
| [ebs-volumes](compute.md#ebs-volumes) | Show EBS volume state, size, and availability zone. | Native |
| [ec](service-shortcuts.md#ec) | Use elasticache operations through a short service name. | Service shortcut |
| [ecr-list-repositories](reports.md#ecr-list-repositories) | List private ECR repository ARNs. | Native |
| [ecr-scan-findings](reports.md#ecr-scan-findings) | Read basic or enhanced image-scan findings. | Helper |
| [events-list-csv](reports.md#events-list-csv) | Export EventBridge rules from one event bus. | Helper |
| [find-access-key](identity.md#find-access-key) | Find IAM users who own an access key ID. | Helper |
| [find-host-by-instance-id](compute.md#find-host-by-instance-id) | Return available private DNS names for an instance ID. | Helper |
| [find-instance-by-public-ip](compute.md#find-instance-by-public-ip) | Find instances with a matching public IP. | Helper |
| [find-instances-in-sg](compute.md#find-instances-in-sg) | Find EC2 instances whose network interfaces use a security group. | Helper |
| [find-nat-gateway-by-public-ip](network.md#find-nat-gateway-by-public-ip) | Find NAT gateways containing a public IP. | Helper |
| [find-ssh-open](security-groups.md#find-ssh-open) | Find ingress rules permitting TCP port 22 or all protocols. | Helper |
| [find-users-without-mfa](identity.md#find-users-without-mfa) | Find IAM users with zero assigned MFA devices. | Helper |
| [generate-sts-token](retired.md#generate-sts-token) | Use supported AWS profile providers or configure mfa-login. | Retired |
| [get-asg-instance-ips](compute.md#get-asg-instance-ips) | List available private IPs of instances tagged for an Auto Scaling group. | Helper |
| [get-dns-from-instance-id](compute.md#get-dns-from-instance-id) | Return public DNS names for an instance ID. | Helper |
| [get-group-id](security-groups.md#get-group-id) | Resolve one exact group name inside a specified VPC. | Helper |
| [get-instance-id-from-dns](compute.md#get-instance-id-from-dns) | Find instance IDs by exact public DNS name. | Helper |
| [iam-keys-days-remaining](retired.md#iam-keys-days-remaining) | Use an explicit per-key age and rotation-policy report. | Retired |
| [install](retired.md#install) | Run python3 aws_alias_manager.py install from a clean checkout. | Retired |
| [lambda-list-csv](reports.md#lambda-list-csv) | Export Lambda function configuration. | Helper |
| [last-log](reports.md#last-log) | Tail events from a log group across streams. | Helper |
| [list-all-regions](network.md#list-all-regions) | List region names returned by EC2 discovery. | Native |
| [list-azs](network.md#list-azs) | List availability-zone names for the selected region. | Native |
| [list-hosts-csv](compute.md#list-hosts-csv) | Export EC2 instances with private addressing and Name tags. | Helper |
| [list-iam-users](identity.md#list-iam-users) | List IAM usernames in the selected account. | Native |
| [list-igw](network.md#list-igw) | Show internet gateways and their first attached VPC. | Native |
| [list-instance-status](network.md#list-instance-status) | Show EC2 state and system/instance status checks. | Native |
| [list-instances](compute.md#list-instances) | Inventory EC2 instances across explicit regions or all enabled regions. | Helper |
| [list-ngw](network.md#list-ngw) | Show NAT gateways and their first address. | Native |
| [list-routes](network.md#list-routes) | Show route-table IDs and IPv4 gateway projections. | Native |
| [list-sgs](security-groups.md#list-sgs) | List security-group IDs and names. | Native |
| [list-subnets](network.md#list-subnets) | Show subnet location, parent VPC, and IPv4 CIDR. | Native |
| [list-user-keys](identity.md#list-user-keys) | List access-key metadata for an IAM user. | Helper |
| [list-vgw](network.md#list-vgw) | Show VPN gateways and all attached VPC IDs. | Native |
| [list-virtual-mfa](identity.md#list-virtual-mfa) | List MFA devices assigned to an IAM user. | Helper |
| [list-vpcs](network.md#list-vpcs) | Show VPC IDs, IPv4 CIDRs, Name tags, and default status. | Native |
| [list-vpn-connection](network.md#list-vpn-connection) | Show Site-to-Site VPN connections and gateway IDs. | Native |
| [log-groups](reports.md#log-groups) | List CloudWatch Logs group names. | Native |
| [mfa](identity.md#mfa) | Create temporary IAM-user credentials using an OTP MFA device. | Native |
| [my-ip](utilities.md#my-ip) | Look up the current public IPv4 address. | Helper |
| [profiles](identity.md#profiles) | List configured profile names. | Native |
| [public-ports](security-groups.md#public-ports) | Find ingress peers open to every IPv4 or IPv6 address. | Helper |
| [region](retired.md#region) | Use configure get region or configure set region with an explicit profile. | Retired |
| [revoke-my-ip](security-groups.md#revoke-my-ip) | Remove the matching single-host ingress rule. | Helper |
| [revoke-my-ip-all](retired.md#revoke-my-ip-all) | Use revoke-my-ip with an explicit group ID, protocol and port. | Retired |
| [rotate-iam-keys](retired.md#rotate-iam-keys) | Use your separately reviewed IAM key-rotation procedure. | Retired |
| [running-instances](compute.md#running-instances) | Show running EC2 instances in a table. | Native |
| [sc](service-shortcuts.md#sc) | Use servicecatalog operations through a short service name. | Service shortcut |
| [search-instances](compute.md#search-instances) | Find running or stopped instances by a literal Name substring. | Helper |
| [sg](retired.md#sg) | Use aws ec2 with an explicit operation. | Retired |
| [sg-rules](security-groups.md#sg-rules) | Expand every ingress and egress peer for one group. | Helper |
| [sh](service-shortcuts.md#sh) | Use securityhub operations through a short service name. | Service shortcut |
| [sh-findings-csv](reports.md#sh-findings-csv) | Export Security Hub findings with one row per resource. | Helper |
| [sh-quick-report](reports.md#sh-quick-report) | Summarize Security Hub findings by severity. | Helper |
| [tostring](utilities.md#tostring) | Encode a local JSON document as one JSON string. | Helper |
| [update-aliases](maintenance.md#update-aliases) | Check, update, pin, or roll back the managed alias bundle. | Maintenance |
| [upgrade](maintenance.md#upgrade) | Update the active AWS CLI installation. | Maintenance |
| [vpc-peers](network.md#vpc-peers) | List sorted Name-tag values of VPC peering connections. | Native |
| [whoami](identity.md#whoami) | Return the identity used by the selected profile. | Native |

## Implementation and migration records

- [Modernization record](modernization.md)
- [Migration contracts and CSV schemas](migration.md)
- [Implementation checklist](implementation-checklist.md)
- [Profile and SSO audit](profiles-and-sso.md)

## Example provenance

Helper examples use the command doubles and synthetic responses in `test/fixtures/responses.json`. Native query examples use `test/fixtures/native-responses.json` through a localhost endpoint and the real AWS CLI. Resource identifiers are normalized to illustrative placeholders. `my-ip`, profile listing, MFA prompts, and maintenance messages are explicitly marked illustrative. No live account or credentials were used to produce these examples.
