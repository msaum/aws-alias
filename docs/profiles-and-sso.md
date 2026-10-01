# Profile and SSO audit — October 1, 2026

All 75 current entries were reviewed. The real CLI resolved both modern sso-session and legacy SSO profiles against a local credential-provider fixture. Tests also exercised a role profile with an SSO source, invalid profiles, missing/expired sessions, and profile precedence. All nine native service shortcuts and 18 native query/identity aliases used the selected SSO credentials. Every retained AWS workflow forwarded the selected profile in both supported helper forms.

## Validation

52 tests passed with zero skips on macOS arm64 using AWS CLI 2.37.7. The source audit adds 10 profile/SSO tests to the 42 existing contracts and signer checks. The original 42-test matrix passed on macOS/Linux x86_64 and arm64 before the first PR merged. The expanded suite runs in GitHub CI on macOS/Linux x86_64 and arm64 with the minimum and current AWS CLI versions. Results for this change are recorded in its pull request.

## Invocation rules

Native commands support ordinary AWS global options before or after the alias. For a shell workflow, use --aws-profile PROFILE or put normal options after a separator: aws get-asg-instance-ips GROUP -- --profile PROFILE. The outer AWS CLI consumes ordinary --profile before invoking shell aliases. With an ambient AWS_PROFILE, an unsupported outer --profile may leave a shell workflow in that ambient account. Use the explicit helper option when choosing an account.

SSO login belongs to the AWS CLI: aws sso login --profile PROFILE. The bundle delegates token refresh and role credentials to that provider. An expired session produces the native login guidance and stops dependent service calls.

IAM user reports describe IAM users in the selected account. They can run through an SSO administrative role with suitable IAM permissions. list-virtual-mfa now requires an explicit IAM username, including for IAM-user callers; IAM device APIs do not describe Identity Center users. The native mfa alias serves IAM-user OTP authentication. SSO MFA remains with the identity provider and sso login.

## Every entry

| Alias | Profile and SSO contract | Evidence |
| --- | --- | --- |
| `ag` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `as` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `cfn` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `cp` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `ddb` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `eb` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `ec` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `sc` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `sg` | Migration error, exit 2; no AWS request. | `WorkflowTests / ActualAliasTests` |
| `sh` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `tostring` | No AWS account credentials required. Reads a local JSON file. | `WorkflowTests / UpgradeTests / BundleTests / NativeModelTests` |
| `region` | Migration error, exit 2; no AWS request. | `WorkflowTests / ActualAliasTests` |
| `profiles` | No AWS account credentials required. Lists configured profile names. | `WorkflowTests / UpgradeTests / BundleTests / NativeModelTests` |
| `upgrade` | No AWS account credentials required. Updates CLI installation. | `WorkflowTests / UpgradeTests / BundleTests / NativeModelTests` |
| `update-aliases` | No AWS account credentials required. Updates managed bundle. | `WorkflowTests / UpgradeTests / BundleTests / NativeModelTests` |
| `install` | Migration error, exit 2; no AWS request. | `WorkflowTests / ActualAliasTests` |
| `rotate-iam-keys` | Migration error, exit 2; no AWS request. | `WorkflowTests / ActualAliasTests` |
| `iam-keys-days-remaining` | Migration error, exit 2; no AWS request. | `WorkflowTests / ActualAliasTests` |
| `mfa` | IAM-user OTP login via configure mfa-login. Identity Center uses aws sso login. | `NativeModelTests; AWS configure mfa-login contract` |
| `whoami` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `create-assume-role` | Migration error, exit 2; no AWS request. | `WorkflowTests / ActualAliasTests` |
| `find-access-key` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. Reports IAM users, subject to IAM permissions. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `list-iam-users` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. Reports IAM users, subject to IAM permissions. | `ProfileSSOTests; LocalEndpointTests` |
| `list-user-keys` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. Reports IAM users, subject to IAM permissions. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `list-virtual-mfa` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. Explicit IAM username required. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `delete-virtual-mfa` | Migration error, exit 2; no AWS request. | `WorkflowTests / ActualAliasTests` |
| `find-users-without-mfa` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. Reports IAM users, subject to IAM permissions. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `generate-sts-token` | Migration error, exit 2; no AWS request. | `WorkflowTests / ActualAliasTests` |
| `assume` | Migration error, exit 2; no AWS request. | `WorkflowTests / ActualAliasTests` |
| `running-instances` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `ebs-volumes` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `amazon-linux-amis` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `list-sgs` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `sg-rules` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `get-group-id` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `authorize-my-ip-by-name` | Migration error, exit 2; no AWS request. | `WorkflowTests / ActualAliasTests` |
| `public-ports` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `my-ip` | No AWS account credentials required. Requests public IP over HTTPS. | `WorkflowTests / UpgradeTests / BundleTests / NativeModelTests` |
| `allow-my-ip` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. Profile and region must be explicit helper arguments. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `revoke-my-ip` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. Profile and region must be explicit helper arguments. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `allow-my-ip-all` | Migration error, exit 2; no AWS request. | `WorkflowTests / ActualAliasTests` |
| `revoke-my-ip-all` | Migration error, exit 2; no AWS request. | `WorkflowTests / ActualAliasTests` |
| `delete-ami` | Migration error, exit 2; no AWS request. | `WorkflowTests / ActualAliasTests` |
| `list-instances` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `search-instances` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `list-all-regions` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `list-azs` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `vpc-peers` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `find-instances-in-sg` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `find-ssh-open` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `get-asg-instance-ips` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `find-host-by-instance-id` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `find-instance-by-public-ip` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `find-nat-gateway-by-public-ip` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `list-hosts-csv` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `list-igw` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `list-ngw` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `list-vgw` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `list-vpn-connection` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `list-instance-status` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `list-vpcs` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `list-subnets` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `list-routes` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `get-dns-from-instance-id` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `get-instance-id-from-dns` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `log-groups` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `last-log` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `docker-ecr-login` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. Profile and region must be explicit helper arguments. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `ecr-list-repositories` | Native AWS CLI provider; ordinary --profile before/after alias; SSO sessions and role profiles. | `ProfileSSOTests; LocalEndpointTests` |
| `ecr-scan-findings` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `sh-quick-report` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `sh-findings-csv` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `lambda-list-csv` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `events-list-csv` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |
| `ami-snapshots` | SSO/role profile via --aws-profile or separator flags; ambient named profiles supported. | `EveryWorkflowProfileTests; ProfileSSOTests` |

## Deployment and source boundaries

The repository default is main. Pin update-aliases --ref to a reviewed full commit SHA when reproducible installation is required.

Sources: [AWS SSO profile configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html), [AWS alias implementation](https://github.com/aws/aws-cli/blob/v2/awscli/alias.py), and [configure mfa-login](https://docs.aws.amazon.com/cli/latest/reference/configure/mfa-login.html).
