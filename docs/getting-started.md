# Getting started

This bundle provides shortcuts for AWS service commands, workflows that transform service responses, and a manager for installation and updates. The [command index](README.md#every-alias) links all 75 aliases to their reference pages.

## Requirements

Use AWS CLI 2.37.7 or newer and Python 3.11 or newer on macOS or Linux, on x86_64 or arm64. Docker is needed for ECR login. The companion uses the Python standard library. AWS commands need a configured profile and permission for the service APIs they call.

## Install the complete bundle

```sh
git clone --branch main https://github.com/msaum/aws-alias.git
cd aws-alias
python3 aws_alias_manager.py install
```

Run installation from a clean, committed checkout. It validates the CLI version, alias definitions, companion, and checksums. An existing alias file causes a diff and exit 3. Review the diff before choosing replacement:

```sh
python3 aws_alias_manager.py install --replace-local
```

Replacement saves a timestamped backup. The installed alias link points at the same version directory as the companion. Downloading only the `alias` file leaves its helper dependencies incomplete. See [maintenance](maintenance.md#bootstrap) for the installed layout and recovery.

## Select a profile and region

All profile names and identifiers in this documentation are synthetic examples. Replace them with your own configured values.

For an IAM Identity Center profile, authenticate through the AWS CLI:

```sh
aws sso login --profile example-sso
```

Native aliases accept ordinary AWS global options:

```sh
aws --profile example-sso whoami
aws running-instances --profile example-sso --region us-east-1
```

Shell workflows accept prefixed helper options:

```sh
aws ami-snapshots ami-0123456789abcdef0 --aws-profile example-sso --aws-region us-east-1
```

Or place normal AWS options after a separator:

```sh
aws ami-snapshots ami-0123456789abcdef0 -- --profile example-sso --region us-east-1
```

The outer AWS CLI consumes ordinary global options before invoking a shell alias. Choose one of these supported helper forms when selecting an account. An ordinary outer `--profile` can leave a helper using an ambient profile instead.

Helpers select the profile from their argument, then `AWS_PROFILE`, then `AWS_DEFAULT_PROFILE`. They require a named profile. Region selection uses the helper argument, `AWS_REGION`, `AWS_DEFAULT_REGION`, then the profile's region configuration. `list-instances` uses its positional region list for each request.

```sh
export AWS_PROFILE=example-sso
export AWS_DEFAULT_REGION=us-east-1
aws search-instances demo
```

The grant/revoke helpers and ECR login require profile and region supplied explicitly as helper arguments, even when environment values exist.

## Common helper options

| Option | Purpose |
| --- | --- |
| `--aws-profile NAME` | Select the named AWS credential profile. |
| `--aws-region REGION` | Select the request region. |
| `--aws-output json\|text\|table` | Format transformed results; JSON is the default. |
| `--aws-endpoint-url URL` | Forward an endpoint override to each AWS service request. Multi-service workflows need an endpoint that supports each service they call. |
| `--aws-ca-bundle FILE` | Forward a trusted CA bundle path to the AWS CLI. |

Normal equivalents work after `--`. Arbitrary AWS global options, such as helper `--query`, are outside this parser's supported options. Inspect exact workflow arguments directly from the installed companion:

```sh
python3 "$HOME/.aws/cli/aws-alias/current/aws_alias_manager.py" run search-instances --help
```

## Output and scripts

Helpers fetch AWS responses as JSON before transforming them. Most emit JSON, with successful empty searches returning `[]`. A string result is JSON-quoted by default:

```json
"ami-0123456789abcdef0"
```

Use `--aws-output text` when a consumer needs an unquoted scalar or tab-separated rows. Helper table output uses a plain header and ` | ` separators. `my-ip` emits plain text; `tostring` emits a JSON string; log tail and Docker login use their native textual output.

Native query aliases define table or text output in their expansion. For other formatting or a different projection, use the full AWS service operation. `whoami` and service shortcuts preserve normal AWS output/query controls.

CSV aliases have fixed columns and reject `--aws-output`. Scope and error messages go to stderr, so a redirect captures the report:

```sh
aws list-hosts-csv --aws-profile example-sso --aws-region us-east-1 > hosts.csv
```

Use a CSV parser for fields containing commas, quotes, or newlines. Exact report schemas appear in [migration contracts](migration.md#workflow-inputs-and-outputs).

## Effects and permissions

Most inventory aliases read service metadata. These commands have additional effects:

| Command | Effect |
| --- | --- |
| `allow-my-ip`, `revoke-my-ip` | Change an exact security-group ingress permission. |
| `mfa` | Request temporary IAM-user credentials and write a local profile. |
| `docker-ecr-login` | Write Docker client authentication state. |
| `upgrade` | Update the active CLI installation. |
| `update-aliases` and bootstrap | Write managed alias versions, links, and backups. |
| Service shortcuts | Follow the effect of the AWS operation you choose. |

Profile resolution establishes credentials; service authorization still depends on IAM permissions. Each reference explains which service requests a workflow makes. The tests use synthetic responses and do not prove permission in your account.

## Exit status

| Status | Meaning |
| --- | --- |
| `0` | Success, including ordinary empty inventories. |
| `1` | Manager/workflow failure, unresolved lookup, pending scan, or partial regional failure. |
| `2` | Usage, validation, or retired-command error. |
| `3` | Local bundle conflict or modification. |
| `4` | Another process holds the update lock. |
| Other nonzero status | Propagated AWS command failure; native aliases use AWS CLI behavior. |

`list-instances` can emit completed-region data and still return nonzero. Check its exit status before treating the file as a complete inventory. See [troubleshooting](troubleshooting.md).
