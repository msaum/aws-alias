# Service shortcuts

All examples use synthetic fixtures and illustrative identifiers. Account IDs, profile names, resource IDs, IPs, and hostnames identify no live resources. JSON/text/table examples were captured through the implementation using command doubles or a localhost service, with placeholder normalization for readability. Prompts and provider-specific messages are illustrative. Replace example arguments with your own values before running commands.

[Documentation index](README.md) · [Account and region selection](getting-started.md#select-a-profile-and-region)

Each shortcut replaces a service name. It still requires a service operation and its arguments. Calling a shortcut without an operation shows AWS usage guidance. The nine example operations below read metadata.

## Commands

[ag](#ag) · [as](#as) · [cfn](#cfn) · [cp](#cp) · [ddb](#ddb) · [eb](#eb) · [ec](#ec) · [sc](#sc) · [sh](#sh)

## ag

Use apigateway operations through a short service name.

Expands to `aws apigateway`. Example below: list REST API Gateway APIs. These shortcuts expose the full service API; their effects depend on the operation you choose. Use native AWS global flags. Read the [operation reference](https://docs.aws.amazon.com/cli/latest/reference/apigateway/get-rest-apis.html) for parameters and output.

```sh
aws ag get-rest-apis --profile example-sso --region us-east-1
```

Illustrative response excerpt (additional native fields can be present):

```json
{
  "items": [
    {
      "id": "a1b2c3d4",
      "name": "demo-api"
    }
  ]
}
```

## as

Use autoscaling operations through a short service name.

Expands to `aws autoscaling`. Example below: list Auto Scaling groups. These shortcuts expose the full service API; their effects depend on the operation you choose. Use native AWS global flags. Read the [operation reference](https://docs.aws.amazon.com/cli/latest/reference/autoscaling/describe-auto-scaling-groups.html) for parameters and output.

```sh
aws as describe-auto-scaling-groups --profile example-sso --region us-east-1
```

Illustrative response excerpt (additional native fields can be present):

```json
{
  "AutoScalingGroups": [
    {
      "AutoScalingGroupName": "demo-web",
      "MinSize": 1,
      "MaxSize": 4,
      "DesiredCapacity": 2
    }
  ]
}
```

## cfn

Use cloudformation operations through a short service name.

Expands to `aws cloudformation`. Example below: list CloudFormation stack summaries. These shortcuts expose the full service API; their effects depend on the operation you choose. Use native AWS global flags. Read the [operation reference](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/list-stacks.html) for parameters and output.

```sh
aws cfn list-stacks --profile example-sso --region us-east-1
```

Illustrative response excerpt (additional native fields can be present):

```json
{
  "StackSummaries": [
    {
      "StackName": "demo-stack",
      "StackStatus": "CREATE_COMPLETE"
    }
  ]
}
```

## cp

Use codepipeline operations through a short service name.

Expands to `aws codepipeline`. Example below: list CodePipeline pipelines. These shortcuts expose the full service API; their effects depend on the operation you choose. Use native AWS global flags. Read the [operation reference](https://docs.aws.amazon.com/cli/latest/reference/codepipeline/list-pipelines.html) for parameters and output.

```sh
aws cp list-pipelines --profile example-sso --region us-east-1
```

Illustrative response excerpt (additional native fields can be present):

```json
{
  "pipelines": [
    {
      "name": "demo-pipeline",
      "version": 1
    }
  ]
}
```

## ddb

Use dynamodb operations through a short service name.

Expands to `aws dynamodb`. Example below: list DynamoDB table names. These shortcuts expose the full service API; their effects depend on the operation you choose. Use native AWS global flags. Read the [operation reference](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/list-tables.html) for parameters and output.

```sh
aws ddb list-tables --profile example-sso --region us-east-1
```

Illustrative response excerpt (additional native fields can be present):

```json
{
  "TableNames": [
    "demo-orders",
    "demo-users"
  ]
}
```

## eb

Use elasticbeanstalk operations through a short service name.

Expands to `aws elasticbeanstalk`. Example below: list Elastic Beanstalk environments. These shortcuts expose the full service API; their effects depend on the operation you choose. Use native AWS global flags. Read the [operation reference](https://docs.aws.amazon.com/cli/latest/reference/elasticbeanstalk/describe-environments.html) for parameters and output.

```sh
aws eb describe-environments --profile example-sso --region us-east-1
```

Illustrative response excerpt (additional native fields can be present):

```json
{
  "Environments": [
    {
      "EnvironmentName": "demo-web",
      "Status": "Ready",
      "Health": "Green"
    }
  ]
}
```

## ec

Use elasticache operations through a short service name.

Expands to `aws elasticache`. Example below: list ElastiCache cache clusters. These shortcuts expose the full service API; their effects depend on the operation you choose. Use native AWS global flags. Read the [operation reference](https://docs.aws.amazon.com/cli/latest/reference/elasticache/describe-cache-clusters.html) for parameters and output.

```sh
aws ec describe-cache-clusters --profile example-sso --region us-east-1
```

Illustrative response excerpt (additional native fields can be present):

```json
{
  "CacheClusters": [
    {
      "CacheClusterId": "demo-cache",
      "Engine": "redis",
      "CacheClusterStatus": "available"
    }
  ]
}
```

## sc

Use servicecatalog operations through a short service name.

Expands to `aws servicecatalog`. Example below: list Service Catalog portfolios. These shortcuts expose the full service API; their effects depend on the operation you choose. Use native AWS global flags. Read the [operation reference](https://docs.aws.amazon.com/cli/latest/reference/servicecatalog/list-portfolios.html) for parameters and output.

```sh
aws sc list-portfolios --profile example-sso --region us-east-1
```

Illustrative response excerpt (additional native fields can be present):

```json
{
  "PortfolioDetails": [
    {
      "Id": "port-demo123",
      "DisplayName": "Demo portfolio",
      "ProviderName": "Example platform team"
    }
  ]
}
```

## sh

Use securityhub operations through a short service name.

Expands to `aws securityhub`. Example below: inspect Security Hub configuration. These shortcuts expose the full service API; their effects depend on the operation you choose. Use native AWS global flags. Read the [operation reference](https://docs.aws.amazon.com/cli/latest/reference/securityhub/describe-hub.html) for parameters and output.

```sh
aws sh describe-hub --profile example-sso --region us-east-1
```

Illustrative response excerpt (additional native fields can be present):

```json
{
  "HubArn": "arn:aws:securityhub:us-east-1:123456789012:hub/default",
  "SubscribedAt": "2026-01-01T00:00:00Z",
  "AutoEnableControls": true
}
```

