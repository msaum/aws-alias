# Logs, registries, and CSV reports

All examples use synthetic fixtures and illustrative identifiers. Account IDs, profile names, resource IDs, IPs, and hostnames identify no live resources. JSON/text/table examples were captured through the implementation using command doubles or a localhost service, with placeholder normalization for readability. Prompts and provider-specific messages are illustrative. Replace example arguments with your own values before running commands.

[Documentation index](README.md) · [Account and region selection](getting-started.md#select-a-profile-and-region)

Read commands require permission for their corresponding service operations. `docker-ecr-login` also writes local Docker authentication state. CSV commands write a header even when their service returns no records.

## Commands

[log-groups](#log-groups) · [last-log](#last-log) · [docker-ecr-login](#docker-ecr-login) · [ecr-list-repositories](#ecr-list-repositories) · [ecr-scan-findings](#ecr-scan-findings) · [sh-quick-report](#sh-quick-report) · [sh-findings-csv](#sh-findings-csv) · [lambda-list-csv](#lambda-list-csv) · [events-list-csv](#events-list-csv)

## log-groups

List CloudWatch Logs group names.

Uses `logs describe-log-groups` and emits names as text. Native operation filters such as `--log-group-name-prefix` can narrow the list.

```sh
aws log-groups --profile example-sso --region us-east-1
```

Synthetic example output:

```text
fixture/logs
```

Native expansion:

```text
aws logs describe-log-groups --query 'logGroups[].logGroupName' --output text
```

## last-log

Tail events from a log group across streams.

Requires a log-group name. Uses `logs tail`, default `--since 10m`; `--since` accepts the CLI time format and `--follow` continues streaming. Output uses the native log-tail format, independent of helper `--aws-output`. Stop a follow session with Ctrl-C.

```sh
aws last-log /fixture/log --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```text
fixture event
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws last-log [-h] [--profile PROFILE] [--region REGION]
                    [--endpoint-url ENDPOINT_URL] [--ca-bundle CA_BUNDLE]
                    [--output {json,text,table}] [--since SINCE] [--follow]
                    log_group
```

## docker-ecr-login

Authenticate the local Docker client to a private ECR registry.

Changes local Docker authentication state. Requires registry hostname, explicit profile, and explicit region; the registry region must agree. Calls ECR `get-login-password` and passes the password through Docker stdin. Docker must be installed. The password is excluded from command arguments and example output.

```sh
aws docker-ecr-login 000000000000.dkr.ecr.us-east-1.amazonaws.com --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```text
Login Succeeded
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws docker-ecr-login [-h] [--profile PROFILE] [--region REGION]
                            [--endpoint-url ENDPOINT_URL]
                            [--ca-bundle CA_BUNDLE]
                            [--output {json,text,table}]
                            registry
```

## ecr-list-repositories

List private ECR repository ARNs.

Uses `ecr describe-repositories` and emits repository ARNs as text. Scope is the selected account and region.

```sh
aws ecr-list-repositories --profile example-sso --region us-east-1
```

Synthetic example output:

```text
arn:aws:ecr:us-east-1:123456789012:repository/fixture
```

Native expansion:

```text
aws ecr describe-repositories --query 'repositories[].repositoryArn' --output text
```

## ecr-scan-findings

Read basic or enhanced image-scan findings.

Requires a repository and exactly one of `--image-tag` or `--image-digest`. Calls `describe-image-scan-findings`; this helper does not initiate scans. Returns `status`, `imageId`, and findings with `severity`, `name`, `description`, `findingArn`. `COMPLETE` and `ACTIVE` succeed. Pending/failed/unknown status is emitted and produces exit 1.

```sh
aws ecr-scan-findings repo --image-digest sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
{
  "status": "ACTIVE",
  "imageId": {
    "imageDigest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  },
  "findings": [
    {
      "severity": "HIGH",
      "name": "CVE-fixture",
      "description": null,
      "findingArn": "arn:fixture"
    }
  ]
}
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws ecr-scan-findings [-h] [--profile PROFILE] [--region REGION]
                             [--endpoint-url ENDPOINT_URL]
                             [--ca-bundle CA_BUNDLE]
                             [--output {json,text,table}]
                             (--image-tag IMAGE_TAG |
                             --image-digest IMAGE_DIGEST)
                             repository
```

## sh-quick-report

Summarize Security Hub findings by severity.

Includes ACTIVE records with NEW workflow status from the selected account/region response. Emits five rows: CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL. Each includes Count and sorted unique Titles. Counts describe findings, while Titles remove duplicates. Aggregation configuration can affect the response scope.

```sh
aws sh-quick-report --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  {
    "Severity": "CRITICAL",
    "Count": 1,
    "Titles": [
      "Critical"
    ]
  },
  {
    "Severity": "HIGH",
    "Count": 0,
    "Titles": []
  },
  {
    "Severity": "MEDIUM",
    "Count": 0,
    "Titles": []
  },
  {
    "Severity": "LOW",
    "Count": 0,
    "Titles": []
  },
  {
    "Severity": "INFORMATIONAL",
    "Count": 1,
    "Titles": [
      "quote, \"example\"\nnew line"
    ]
  }
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws sh-quick-report [-h] [--profile PROFILE] [--region REGION]
                           [--endpoint-url ENDPOINT_URL]
                           [--ca-bundle CA_BUNDLE]
                           [--output {json,text,table}]
```

## sh-findings-csv

Export Security Hub findings with one row per resource.

Uses the same ACTIVE/NEW selection as `sh-quick-report`. Expands multiple resources; a finding with no resources still gets one row. CSV fields include timestamps, severity, finding ID, resource type/ID, and remediation recommendation. Resource expansion can make the row count greater than the finding count.

```sh
aws sh-findings-csv --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```text
Title,Description,Region,GeneratorId,FirstObservedAt,LastObservedAt,CreatedAt,UpdatedAt,Severity.Label,Id,Resources.Type,Resources.Id,Remediation.Text,Remediation.Url
"quote, ""example""
new line",description,us-east-1,generator,,,,,INFORMATIONAL,finding-1,AwsEc2Instance,i-0123456789abcdef0,"Fix, then verify",https://example.com/fix
"quote, ""example""
new line",description,us-east-1,generator,,,,,INFORMATIONAL,finding-1,AwsEc2Instance,i-0123456789abcdef1,"Fix, then verify",https://example.com/fix
Critical,,,,,,,,CRITICAL,finding-2,,,,
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws sh-findings-csv [-h] [--profile PROFILE] [--region REGION]
                           [--endpoint-url ENDPOINT_URL]
                           [--ca-bundle CA_BUNDLE]
                           [--output {json,text,table}]
```

## lambda-list-csv

Export Lambda function configuration.

Fixed columns include FunctionName, Description, FunctionArn, Runtime, Role, Handler, CodeSize, Timeout, MemorySize, LastModified, TracingConfig.Mode, PackageType. Image functions can have empty Runtime/Handler cells. This is a function inventory, with no per-version or execution metrics.

```sh
aws lambda-list-csv --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```text
FunctionName,Description,FunctionArn,Runtime,Role,Handler,CodeSize,Timeout,MemorySize,LastModified,TracingConfig.Mode,PackageType
image-function,"comma, ""quote""",arn:fixture,,,,,,128,,Active,Image
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws lambda-list-csv [-h] [--profile PROFILE] [--region REGION]
                           [--endpoint-url ENDPOINT_URL]
                           [--ca-bundle CA_BUNDLE]
                           [--output {json,text,table}]
```

## events-list-csv

Export EventBridge rules from one event bus.

Optional `--event-bus`, default `default`. Reports the bus on stderr and emits Name, EventBusName, Description, Arn, State, ScheduleExpression. The command lists rules; target configuration and EventBridge Scheduler schedules require separate APIs.

```sh
aws events-list-csv --event-bus custom --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```text
Name,EventBusName,Description,Arn,State,ScheduleExpression
event-rule,custom,"line
one",arn:fixture,ENABLED,
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws events-list-csv [-h] [--profile PROFILE] [--region REGION]
                           [--endpoint-url ENDPOINT_URL]
                           [--ca-bundle CA_BUNDLE]
                           [--output {json,text,table}]
                           [--event-bus EVENT_BUS]
```

## Save and read CSV output

```sh
aws lambda-list-csv --aws-profile example-sso --aws-region us-east-1 > functions.csv
```

The file contains stdout only; scope messages remain on stderr. Python CSV encoding quotes commas, quotes, and embedded newlines. A logical CSV row can occupy multiple physical lines. Use a CSV parser rather than splitting lines or commas. Exact schemas are recorded in [migration contracts](migration.md#workflow-inputs-and-outputs).
