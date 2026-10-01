# Release migration contracts

This release applies the October 1 review to all 74 original aliases and adds `ami-snapshots`. The approved plan keeps `upgrade` and `update-aliases` through the companion manager. Their original retirement proposals are superseded. Thirteen compatibility entries return migration errors; remove them in the next tagged release.

## Workflow inputs and outputs

Helper output defaults to JSON. `--aws-output text|table` formats the resulting values. CSV commands write headers and fixed columns, with empty cells for missing values. Python's CSV writer quotes commas, quotes, and embedded newlines. Every AWS response used for transformation is fetched as JSON with automatic CLI pagination enabled.

| Workflow | Arguments and result |
| --- | --- |
| `tostring` | JSON file path; emits one JSON string containing compact JSON; read/parse errors fail. |
| `my-ip` | Emits a validated public IPv4 address from HTTPS checkip.amazonaws.com. |
| `list-user-keys` | Username; returns the user's AccessKeyMetadata array. |
| `list-virtual-mfa` | Required IAM username; returns assigned MFADevices, including hardware devices. The historical name remains for compatibility. |
| `find-access-key` | 20-character key ID; checks every IAM user and returns matching usernames. Lookup failure stops the scan. |
| `find-users-without-mfa` | Enumerates all IAM users and checks assigned devices per user, including hardware devices. Reports users with zero assigned devices. |
| `sg-rules` | Group ID; emits ingress/egress rows with IPv4, IPv6, group and prefix-list peers. |
| `get-group-id` | Exact group name and VPC ID; exactly one match is required. |
| `public-ports` | Public ingress peers `0.0.0.0/0` and `::/0`, preserving protocol and port ranges. |
| `find-ssh-open` | Public ingress TCP rules whose range includes 22, and all-protocol rules. |
| `allow-my-ip`, `revoke-my-ip` | Group ID, tcp/udp, port, optional single-host CIDR; explicit profile/region. Only the exact requested rule changes. Duplicate grants and absent revocations return Changed=false; other errors fail. |
| `ami-snapshots` | AMI ID; emits sorted distinct EBS snapshot IDs. |
| `list-instances` | Exact region names or `all`; emits Region, InstanceId, Name, InstanceType, PublicIpAddress and State. `all` discovers enabled regions. Region failures are reported with completed data and exit 1. |
| `search-instances` | Literal substring of the Name tag; running/stopped instances; missing Name is nullable. |
| `find-instances-in-sg` | Group ID, optional label tag key; stable instance IDs and nullable labels/IPs. |
| `get-asg-instance-ips` | ASG name; uses the group tag filter and returns available private IPs. |
| `find-host-by-instance-id` | Instance ID; returns actual PrivateDnsName values. |
| `find-instance-by-public-ip` | Valid IP; stable instance IDs with nullable Name and IP fields. |
| `find-nat-gateway-by-public-ip` | Valid IP; paginates NAT gateways and matches any address locally; stable gateway ID and nullable Name. |
| `get-dns-from-instance-id` | Instance ID; available PublicDnsName values as an array. |
| `get-instance-id-from-dns` | Exact public DNS name; matching instance IDs as an array. |
| `amazon-linux-amis` | Optional `x86_64` or `arm64`; resolves AL2023 kernel-default through the selected region's public SSM parameter. |
| `last-log` | Log-group name, optional `--since` (default 10m) and `--follow`; uses logs tail across streams. |
| `docker-ecr-login` | Private registry hostname, explicit profile/region; checks region agreement, obtains a password, and passes it solely through Docker stdin. |
| `ecr-scan-findings` | Repository and exactly one `--image-tag` or `--image-digest`; status, imageId and findings from basic/enhanced scans. COMPLETE/ACTIVE succeed; pending/failed status is emitted and returns nonzero. |
| `sh-quick-report` | ACTIVE records with NEW workflow status, selected account/region; counts Findings for CRITICAL, HIGH, MEDIUM, LOW and INFORMATIONAL. |
| `sh-findings-csv` | Same Security Hub scope; one row per resource, including a nullable resource row when absent. |
| `lambda-list-csv` | Functions in the selected account/region; nullable runtime/handler for image functions. |
| `events-list-csv` | Optional `--event-bus`, default `default`; reports the selected bus on stderr. |

Public security-group rule matches describe exposure permitted by those rules. Internet reachability also depends on routing and other network controls. These reports inspect the selected account/region. Native CLI credential providers resolve the selected profile. IAM listings cover that account, and discovery errors remain visible.

CSV schemas:

- `list-hosts-csv`: InstanceId, InstanceType, PrivateIpAddress, SubnetId, Name.
- `sh-findings-csv`: Title, Description, Region, GeneratorId, FirstObservedAt, LastObservedAt, CreatedAt, UpdatedAt, Severity.Label, Id, Resources.Type, Resources.Id, Remediation.Text, Remediation.Url.
- `lambda-list-csv`: FunctionName, Description, FunctionArn, Runtime, Role, Handler, CodeSize, Timeout, MemorySize, LastModified, TracingConfig.Mode, PackageType.
- `events-list-csv`: Name, EventBusName, Description, Arn, State, ScheduleExpression.

## Native aliases

The native service shortcuts are ag→apigateway, as→autoscaling, cfn→cloudformation, cp→codepipeline, ddb→dynamodb, eb→elasticbeanstalk, ec→elasticache, sc→servicecatalog and sh→securityhub. `sg` now gives a migration error directing callers to an explicit EC2 operation.

`whoami` expands to `sts get-caller-identity`; `profiles` uses `configure list-profiles`. `mfa` expands to `configure mfa-login` for IAM-user MFA. Its supported AWS behavior may create a session profile. Identity Center users should use their SSO profile workflow.

Query aliases declare table or text output in the alias definition. These options determine formatting when the alias expands, even if the outer invocation supplied an output option. To change a native query or its formatting, invoke the expanded service operation directly. Service shortcuts and `whoami` retain ordinary AWS output/query controls.

Table aliases: list-iam-users, running-instances, ebs-volumes, list-igw, list-ngw, list-vgw, list-vpn-connection, list-instance-status, list-vpcs, list-subnets and list-routes. Text aliases: list-sgs, list-all-regions, list-azs, vpc-peers, log-groups and ecr-list-repositories.

`ebs-volumes` selects Name by tag key. `list-vgw` sorts attached VPC IDs and joins them with commas. Name tags remain nullable, and empty responses succeed. `list-routes` retains the existing IPv4 destination/gateway projection. `list-ngw` retains its first-address projection; use the service operation for full address inventories. Native failures retain AWS CLI behavior and status.

## Retired workflows

`region` directs users to `configure get region` / `configure set region` with an explicit profile. `assume` and `generate-sts-token` direct users to configured role profiles or supported session providers. Migration requires checking any consumers of previously exported credentials.

`rotate-iam-keys`, `iam-keys-days-remaining`, `create-assume-role` and `delete-virtual-mfa` require dedicated reviewed key, role or MFA administration workflows. The historical 60-day key-expiry assumption has been removed. `authorize-my-ip-by-name`, `allow-my-ip-all` and `revoke-my-ip-all` direct users to the scoped grant/revoke pair. `delete-ami` points to `ami-snapshots`. `install` points to clean-checkout bootstrap. Compatibility entries exit 2 before invoking AWS.

## Every original alias

The table below records the approved disposition, resulting expansion or migration, and the test family that exercises it. Helper choices for positional and multi-step commands preserve quoted arguments through the companion.

| Alias | Approved action | Result | Evidence |
| --- | --- | --- | --- |
| `ag` | Keep | apigateway | `NativeModelTests` |
| `as` | Keep | autoscaling | `NativeModelTests` |
| `cfn` | Keep | cloudformation | `NativeModelTests` |
| `cp` | Keep | codepipeline | `NativeModelTests` |
| `ddb` | Keep | dynamodb | `NativeModelTests` |
| `eb` | Keep | elasticbeanstalk | `NativeModelTests` |
| `ec` | Keep | elasticache | `NativeModelTests` |
| `sc` | Keep | servicecatalog | `NativeModelTests` |
| `sh` | Keep | securityhub | `NativeModelTests` |
| `sg` | Retire | Use aws ec2 with an explicit operation. | `WorkflowTests.test_retired_entries_do_not_invoke_aws; ActualAliasTests` |
| `upgrade` | Fix | Provider detection, CLI-native/Homebrew upgrade, path/version verification; --all combines updates. | `UpgradeTests` |
| `install` | Retire | Run python3 aws_alias_manager.py install from a clean checkout. | `WorkflowTests.test_retired_entries_do_not_invoke_aws; ActualAliasTests` |
| `update-aliases` | Fix | Pinned complete bundles, protected edits, backup, lock, atomic pointer, rollback. | `BundleTests` |
| `rotate-iam-keys` | Retire | Use your separately reviewed IAM key-rotation procedure. | `WorkflowTests.test_retired_entries_do_not_invoke_aws; ActualAliasTests` |
| `iam-keys-days-remaining` | Retire | Use an explicit per-key age and rotation-policy report. | `WorkflowTests.test_retired_entries_do_not_invoke_aws; ActualAliasTests` |
| `mfa` | Replace | configure mfa-login | `NativeModelTests` |
| `assume` | Replace | Configure a role profile and select it with --profile. | `WorkflowTests.test_retired_entries_do_not_invoke_aws; ActualAliasTests` |
| `generate-sts-token` | Replace | Use supported AWS profile providers or configure mfa-login. | `WorkflowTests.test_retired_entries_do_not_invoke_aws; ActualAliasTests` |
| `whoami` | Simplify | sts get-caller-identity | `NativeModelTests; LocalEndpointTests` |
| `profiles` | Simplify | configure list-profiles | `NativeModelTests` |
| `region` | Replace | Use configure get region or configure set region with an explicit profile. | `WorkflowTests.test_retired_entries_do_not_invoke_aws; ActualAliasTests` |
| `tostring` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests` |
| `create-assume-role` | Retire | Define the role and trust policy in reviewed infrastructure code. | `WorkflowTests.test_retired_entries_do_not_invoke_aws; ActualAliasTests` |
| `delete-virtual-mfa` | Retire | Use an administrator MFA deactivation/deletion procedure. | `WorkflowTests.test_retired_entries_do_not_invoke_aws; ActualAliasTests` |
| `find-access-key` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `list-iam-users` | Simplify | iam list-users --query Users[].UserName --output table | `NativeModelTests; LocalEndpointTests` |
| `list-user-keys` | Simplify | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `list-virtual-mfa` | Fix | Explicit IAM username; compatible with SSO callers that can inspect that IAM user. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `find-users-without-mfa` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `running-instances` | Simplify | ec2 describe-instances --filters Name=instance-state-name,Values=running --query 'Reservations[].Instances[].{ID:InstanceId,Hostname:PublicDnsName,Name:Tags[?Key==`Name`].Value&#124;[0],Type:InstanceType,Platform:Platform&#124;&#124;`Linux`}' --output table | `NativeModelTests; LocalEndpointTests` |
| `list-sgs` | Simplify | ec2 describe-security-groups --query 'SecurityGroups[].[GroupId,GroupName]' --output text | `NativeModelTests; LocalEndpointTests` |
| `list-all-regions` | Simplify | ec2 describe-regions --query 'Regions[].RegionName' --output text | `NativeModelTests; LocalEndpointTests` |
| `list-azs` | Simplify | ec2 describe-availability-zones --query 'AvailabilityZones[].ZoneName' --output text | `NativeModelTests; LocalEndpointTests` |
| `vpc-peers` | Simplify | ec2 describe-vpc-peering-connections --query 'sort(VpcPeeringConnections[].Tags[?Key==`Name`].Value[]&#124;&#124;`[]`)' --output text | `NativeModelTests; LocalEndpointTests` |
| `log-groups` | Simplify | logs describe-log-groups --query 'logGroups[].logGroupName' --output text | `NativeModelTests; LocalEndpointTests` |
| `ecr-list-repositories` | Simplify | ecr describe-repositories --query 'repositories[].repositoryArn' --output text | `NativeModelTests; LocalEndpointTests` |
| `ebs-volumes` | Fix | ec2 describe-volumes --query 'Volumes[].{VolumeId:VolumeId,State:State,Size:Size,Name:Tags[?Key==`Name`].Value&#124;[0],AZ:AvailabilityZone}' --output table | `NativeModelTests; LocalEndpointTests` |
| `amazon-linux-amis` | Replace | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `sg-rules` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `get-group-id` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `authorize-my-ip-by-name` | Retire | Use allow-my-ip with an explicit group ID, protocol and port. | `WorkflowTests.test_retired_entries_do_not_invoke_aws; ActualAliasTests` |
| `allow-my-ip-all` | Retire | Use allow-my-ip with an explicit group ID, protocol and port. | `WorkflowTests.test_retired_entries_do_not_invoke_aws; ActualAliasTests` |
| `revoke-my-ip-all` | Retire | Use revoke-my-ip with an explicit group ID, protocol and port. | `WorkflowTests.test_retired_entries_do_not_invoke_aws; ActualAliasTests` |
| `public-ports` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `find-ssh-open` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `my-ip` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests` |
| `allow-my-ip` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `revoke-my-ip` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `delete-ami` | Replace | Use ami-snapshots <ami-id> to list the associated snapshots. | `WorkflowTests.test_retired_entries_do_not_invoke_aws; ActualAliasTests` |
| `list-instances` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `search-instances` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `find-instances-in-sg` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `get-asg-instance-ips` | Simplify | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `find-host-by-instance-id` | Replace | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `find-instance-by-public-ip` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `find-nat-gateway-by-public-ip` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `list-hosts-csv` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `list-igw` | Keep | ec2 describe-internet-gateways  --query "InternetGateways[].{IGW:InternetGatewayId,VpcId: Attachments[].VpcId&#124;[0], Name: Tags[?Key=='Name'].Value &#124;[0] }"   --output table | `NativeModelTests; LocalEndpointTests` |
| `list-ngw` | Keep | ec2 describe-nat-gateways  --query "NatGateways[].{VpcId:VpcId, NatGatewayId: NatGatewayId, SubnetId: SubnetId, PublicIp: NatGatewayAddresses[].PublicIp &#124; [0], PrivateIp: NatGatewayAddresses[].PrivateIp &#124; [0] }"  --output table | `NativeModelTests; LocalEndpointTests` |
| `list-vpn-connection` | Keep | ec2 describe-vpn-connections  --query "VpnConnections[].{ VpnConnectionId: VpnConnectionId, CustomerGatewayId:CustomerGatewayId,VpnGatewayId:VpnGatewayId, Name: Tags[?Key=='Name'].Value&#124; [0] }"  --output table | `NativeModelTests; LocalEndpointTests` |
| `list-instance-status` | Keep | ec2 describe-instance-status  --query "InstanceStatuses[].{InstanceId: InstanceId, State: InstanceState.Name, AZ: AvailabilityZone, SystemStatus: SystemStatus.Status, InstanceStatus: InstanceStatus.Status}"  --output table | `NativeModelTests; LocalEndpointTests` |
| `list-vpcs` | Keep | ec2 describe-vpcs  --query  "Vpcs[].{VpcId: VpcId, CidrBlock: CidrBlock,  Name: Tags[?Key=='Name'].Value&#124; [0], IsDefault: IsDefault}"  --output table | `NativeModelTests; LocalEndpointTests` |
| `list-subnets` | Keep | ec2 describe-subnets  --query "Subnets[].{AZ:AvailabilityZone,VpcId:VpcId,SubnetId:SubnetId,CidrBlock:CidrBlock,    Name: Tags[?Key=='Name'].Value&#124; [0]}"  --output table | `NativeModelTests; LocalEndpointTests` |
| `list-routes` | Keep | ec2 describe-route-tables  --query "RouteTables[].{RouteTableId:RouteTableId, VpcId:VpcId, Name: Tags[?Key=='Name'].Value&#124; [0], GatewayId: Routes[].{GatewayId:GatewayId,DestinationCidrBlock: DestinationCidrBlock} }  "  --output table | `NativeModelTests; LocalEndpointTests` |
| `list-vgw` | Fix | ec2 describe-vpn-gateways --query 'VpnGateways[].{VpnGatewayId:VpnGatewayId,AmazonSideAsn:AmazonSideAsn,VpcIds:join(`,`,sort(VpcAttachments[].VpcId&#124;&#124;`[]`)),Name:Tags[?Key==`Name`].Value&#124;[0]}' --output table | `NativeModelTests; LocalEndpointTests` |
| `get-dns-from-instance-id` | Simplify | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `get-instance-id-from-dns` | Simplify | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `last-log` | Replace | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `docker-ecr-login` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `ecr-scan-findings` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `sh-quick-report` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `sh-findings-csv` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `lambda-list-csv` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
| `events-list-csv` | Fix | Companion workflow; inputs and outputs above. | `WorkflowTests.test_every_aws_workflow_success_and_failure` |
