# EC2 instances, EBS, and AMIs

All examples use synthetic fixtures and illustrative identifiers. Account IDs, profile names, resource IDs, IPs, and hostnames identify no live resources. JSON/text/table examples were captured through the implementation using command doubles or a localhost service, with placeholder normalization for readability. Prompts and provider-specific messages are illustrative. Replace example arguments with your own values before running commands.

[Documentation index](README.md) · [Account and region selection](getting-started.md#select-a-profile-and-region)

These commands read AWS metadata. Specify a region; `list-instances` can scan multiple regions. CLI pagination stays enabled.

## Commands

[running-instances](#running-instances) · [ebs-volumes](#ebs-volumes) · [amazon-linux-amis](#amazon-linux-amis) · [list-instances](#list-instances) · [search-instances](#search-instances) · [find-instances-in-sg](#find-instances-in-sg) · [get-asg-instance-ips](#get-asg-instance-ips) · [find-host-by-instance-id](#find-host-by-instance-id) · [find-instance-by-public-ip](#find-instance-by-public-ip) · [list-hosts-csv](#list-hosts-csv) · [get-dns-from-instance-id](#get-dns-from-instance-id) · [get-instance-id-from-dns](#get-instance-id-from-dns) · [ami-snapshots](#ami-snapshots)

## running-instances

Show running EC2 instances in a table.

Filters EC2 instances to state `running`. Columns: `ID`, `Hostname` (public DNS), `Name`, `Type`, `Platform`. Platform defaults to `Linux` when AWS omits it; Name is selected by tag key and can be null.

```sh
aws running-instances --profile example-sso --region us-east-1
```

Synthetic example output:

```text
-------------------------------------------------------------------------------
|                              DescribeInstances                              |
+----------------+-----------------------+-----------+-----------+------------+
|    Hostname    |          ID           |   Name    | Platform  |   Type     |
+----------------+-----------------------+-----------+-----------+------------+
|  public.example|  i-0123456789abcdef0  |  demo-web |  Linux    |  t3.micro  |
+----------------+-----------------------+-----------+-----------+------------+
```

Native expansion:

```text
aws ec2 describe-instances --filters Name=instance-state-name,Values=running --query 'Reservations[].Instances[].{ID:InstanceId,Hostname:PublicDnsName,Name:Tags[?Key==`Name`].Value|[0],Type:InstanceType,Platform:Platform||`Linux`}' --output table
```

## ebs-volumes

Show EBS volume state, size, and availability zone.

Calls `ec2 describe-volumes`. Table columns: `VolumeId`, `State`, `Size` in GiB, `Name`, `AZ`. Missing Name tags remain null.

```sh
aws ebs-volumes --profile example-sso --region us-east-1
```

Synthetic example output:

```text
------------------------------------------------------------------------------
|                               DescribeVolumes                              |
+------------+---------------+-------+------------+--------------------------+
|     AZ     |     Name      | Size  |   State    |        VolumeId          |
+------------+---------------+-------+------------+--------------------------+
|  us-east-1a|  demo-network |  8    |  available |  vol-0123456789abcdef0   |
+------------+---------------+-------+------------+--------------------------+
```

Native expansion:

```text
aws ec2 describe-volumes --query 'Volumes[].{VolumeId:VolumeId,State:State,Size:Size,Name:Tags[?Key==`Name`].Value|[0],AZ:AvailabilityZone}' --output table
```

## amazon-linux-amis

Resolve the current Amazon Linux 2023 AMI ID for a region.

Optional architecture: `x86_64` (default) or `arm64`. Reads `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-ARCHITECTURE` with SSM `get-parameter`. Returns one JSON string. The value comes from the selected region and can change as AWS publishes images.

```sh
aws amazon-linux-amis arm64 --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
"ami-0123456789abcdef0"
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws amazon-linux-amis [-h] [--profile PROFILE] [--region REGION]
                             [--endpoint-url ENDPOINT_URL]
                             [--ca-bundle CA_BUNDLE]
                             [--output {json,text,table}]
                             [{x86_64,arm64}]
```

## list-instances

Inventory EC2 instances across explicit regions or all enabled regions.

Requires one or more exact region names, or the single value `all`. Calls `describe-instances` per region. `all` discovers regions with `describe-regions` using the selected profile and discovery region. Includes every returned instance state. Output fields: `Region`, `InstanceId`, `Name`, `InstanceType`, `PublicIpAddress`, `State`. If a region fails, completed data goes to stdout, the failure goes to stderr, and exit status is nonzero.

```sh
aws list-instances us-east-1 us-west-2 --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  {
    "Region": "us-east-1",
    "InstanceId": "i-0123456789abcdef0",
    "Name": "quoted, \"name\"\nsecond line",
    "InstanceType": "t3.micro",
    "PublicIpAddress": "203.0.113.5",
    "State": "running"
  },
  {
    "Region": "us-east-1",
    "InstanceId": "i-0123456789abcdef1",
    "Name": null,
    "InstanceType": "t3.micro",
    "PublicIpAddress": null,
    "State": "stopped"
  },
  {
    "Region": "us-west-2",
    "InstanceId": "i-0123456789abcdef0",
    "Name": "quoted, \"name\"\nsecond line",
    "InstanceType": "t3.micro",
    "PublicIpAddress": "203.0.113.5",
    "State": "running"
  },
  {
    "Region": "us-west-2",
    "InstanceId": "i-0123456789abcdef1",
    "Name": null,
    "InstanceType": "t3.micro",
    "PublicIpAddress": null,
    "State": "stopped"
  }
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws list-instances [-h] [--profile PROFILE] [--region REGION]
                          [--endpoint-url ENDPOINT_URL]
                          [--ca-bundle CA_BUNDLE] [--output {json,text,table}]
                          regions [regions ...]
```

## search-instances

Find running or stopped instances by a literal Name substring.

Requires a case-sensitive substring. Searches the Name tag locally after fetching running/stopped instances. Quotes and punctuation are treated literally. Returns instance ID, Name, private IP, and public IP. An absent tag behaves as an empty search value.

```sh
aws search-instances 'quoted, "name"' --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  {
    "InstanceId": "i-0123456789abcdef0",
    "Name": "quoted, \"name\"\nsecond line",
    "PrivateIpAddress": "10.0.0.1",
    "PublicIpAddress": "203.0.113.5"
  }
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws search-instances [-h] [--profile PROFILE] [--region REGION]
                            [--endpoint-url ENDPOINT_URL]
                            [--ca-bundle CA_BUNDLE]
                            [--output {json,text,table}]
                            name
```

## find-instances-in-sg

Find EC2 instances whose network interfaces use a security group.

Requires a group ID; an optional second argument chooses the label tag key, default `Name`. Uses the `network-interface.group-id` EC2 filter. Returns ID, chosen tag value under `Name`, private IP, and public IP.

```sh
aws find-instances-in-sg sg-0123456789abcdef0 --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  {
    "InstanceId": "i-0123456789abcdef0",
    "Name": "quoted, \"name\"\nsecond line",
    "PrivateIpAddress": "10.0.0.1",
    "PublicIpAddress": "203.0.113.5"
  },
  {
    "InstanceId": "i-0123456789abcdef1",
    "Name": null,
    "PrivateIpAddress": "10.0.0.2",
    "PublicIpAddress": null
  }
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws find-instances-in-sg [-h] [--profile PROFILE] [--region REGION]
                                [--endpoint-url ENDPOINT_URL]
                                [--ca-bundle CA_BUNDLE]
                                [--output {json,text,table}]
                                group_id [tag_key]
```

## get-asg-instance-ips

List available private IPs of instances tagged for an Auto Scaling group.

Requires the exact group name. Uses the EC2 tag filter `aws:autoscaling:groupName`. Returns an array of private IP strings for returned instances. It reads EC2 tags rather than Auto Scaling lifecycle or health state.

```sh
aws get-asg-instance-ips 'group,with'"'"'quotes' --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  "10.0.0.1",
  "10.0.0.2"
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws get-asg-instance-ips [-h] [--profile PROFILE] [--region REGION]
                                [--endpoint-url ENDPOINT_URL]
                                [--ca-bundle CA_BUNDLE]
                                [--output {json,text,table}]
                                asg_name
```

## find-host-by-instance-id

Return available private DNS names for an instance ID.

Requires an instance ID and returns an array of actual EC2 `PrivateDnsName` values. DNS availability and reachability depend on the network where the names are used.

```sh
aws find-host-by-instance-id i-0123456789abcdef0 --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  "service.internal"
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws find-host-by-instance-id [-h] [--profile PROFILE] [--region REGION]
                                    [--endpoint-url ENDPOINT_URL]
                                    [--ca-bundle CA_BUNDLE]
                                    [--output {json,text,table}]
                                    instance_id
```

## find-instance-by-public-ip

Find instances with a matching public IP.

Requires an IP address. Uses the EC2 `ip-address` filter. Returns ID, Name, private IP, and public IP. Invalid address syntax fails before an AWS request; EC2 determines which address families its filter supports.

```sh
aws find-instance-by-public-ip 203.0.113.5 --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  {
    "InstanceId": "i-0123456789abcdef0",
    "Name": "quoted, \"name\"\nsecond line",
    "PrivateIpAddress": "10.0.0.1",
    "PublicIpAddress": "203.0.113.5"
  },
  {
    "InstanceId": "i-0123456789abcdef1",
    "Name": null,
    "PrivateIpAddress": "10.0.0.2",
    "PublicIpAddress": null
  }
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws find-instance-by-public-ip [-h] [--profile PROFILE]
                                      [--region REGION]
                                      [--endpoint-url ENDPOINT_URL]
                                      [--ca-bundle CA_BUNDLE]
                                      [--output {json,text,table}]
                                      ip
```

## list-hosts-csv

Export EC2 instances with private addressing and Name tags.

Fixed CSV columns: `InstanceId,InstanceType,PrivateIpAddress,SubnetId,Name`. Includes every instance returned in the selected region. Missing values become empty cells. Quoted fields can span lines.

```sh
aws list-hosts-csv --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```text
InstanceId,InstanceType,PrivateIpAddress,SubnetId,Name
i-0123456789abcdef0,t3.micro,10.0.0.1,subnet-0123456789abcdef0,"quoted, ""name""
second line"
i-0123456789abcdef1,t3.micro,10.0.0.2,,
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws list-hosts-csv [-h] [--profile PROFILE] [--region REGION]
                          [--endpoint-url ENDPOINT_URL]
                          [--ca-bundle CA_BUNDLE] [--output {json,text,table}]
```

## get-dns-from-instance-id

Return public DNS names for an instance ID.

Requires an instance ID. Returns an array of available `PublicDnsName` values; instances without public DNS yield an empty array.

```sh
aws get-dns-from-instance-id i-0123456789abcdef0 --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  "public.example"
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws get-dns-from-instance-id [-h] [--profile PROFILE] [--region REGION]
                                    [--endpoint-url ENDPOINT_URL]
                                    [--ca-bundle CA_BUNDLE]
                                    [--output {json,text,table}]
                                    instance_id
```

## get-instance-id-from-dns

Find instance IDs by exact public DNS name.

Requires a DNS name and uses the EC2 `dns-name` filter. Returns matching IDs as an array. The command queries EC2 metadata and does not perform DNS resolution.

```sh
aws get-instance-id-from-dns public.example --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  "i-0123456789abcdef0",
  "i-0123456789abcdef1"
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws get-instance-id-from-dns [-h] [--profile PROFILE] [--region REGION]
                                    [--endpoint-url ENDPOINT_URL]
                                    [--ca-bundle CA_BUNDLE]
                                    [--output {json,text,table}]
                                    dns_name
```

## ami-snapshots

List EBS snapshot IDs referenced by an AMI.

Requires an AMI ID. Reads its block-device mappings and returns sorted, distinct snapshot IDs. Instance-store mappings are omitted. An empty array is a successful result. The command performs a read-only inventory.

```sh
aws ami-snapshots ami-0123456789abcdef0 --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  "snap-0123456789abcdef0"
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws ami-snapshots [-h] [--profile PROFILE] [--region REGION]
                         [--endpoint-url ENDPOINT_URL] [--ca-bundle CA_BUNDLE]
                         [--output {json,text,table}]
                         ami_id
```

