# Security-group inspection and host rules

All examples use synthetic fixtures and illustrative identifiers. Account IDs, profile names, resource IDs, IPs, and hostnames identify no live resources. JSON/text/table examples were captured through the implementation using command doubles or a localhost service, with placeholder normalization for readability. Prompts and provider-specific messages are illustrative. Replace example arguments with your own values before running commands.

[Documentation index](README.md) · [Account and region selection](getting-started.md#select-a-profile-and-region)

Inspection commands read EC2 metadata. `allow-my-ip` and `revoke-my-ip` change ingress permissions and require explicit context. Ports accept a single value or an ordered range from 0 through 65535.

For inspection helpers such as `find-ssh-open`, use either profile form:

```sh
aws find-ssh-open --aws-profile example-sso --aws-region us-east-1
aws find-ssh-open -- --profile example-sso --region us-east-1
```

The native `list-sgs` alias accepts ordinary `--profile`. The remaining commands on this page are shell workflows and require the helper forms above.

## Commands

[list-sgs](#list-sgs) · [sg-rules](#sg-rules) · [get-group-id](#get-group-id) · [public-ports](#public-ports) · [allow-my-ip](#allow-my-ip) · [revoke-my-ip](#revoke-my-ip) · [find-ssh-open](#find-ssh-open)

## list-sgs

List security-group IDs and names.

Uses `ec2 describe-security-groups` and prints ID/name pairs as text. Native filters can narrow the response, for example `--filters Name=vpc-id,Values=VPC_ID`.

```sh
aws list-sgs --profile example-sso --region us-east-1
```

Synthetic example output:

```text
sg-0123456789abcdef0	demo-group
```

Native expansion:

```text
aws ec2 describe-security-groups --query 'SecurityGroups[].[GroupId,GroupName]' --output text
```

## sg-rules

Expand every ingress and egress peer for one group.

Requires a group ID. Each output row has `GroupId`, `GroupName`, `Direction`, `Protocol`, `FromPort`, `ToPort`, `PeerType`, `Peer`. Supports IPv4, IPv6, group, and prefix-list peers. Protocol `-1` means all protocols and can have null ports.

```sh
aws sg-rules sg-0123456789abcdef0 --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  {
    "GroupId": "sg-0123456789abcdef0",
    "GroupName": "test",
    "Direction": "ingress",
    "Protocol": "tcp",
    "FromPort": 0,
    "ToPort": 100,
    "PeerType": "ipv4",
    "Peer": "0.0.0.0/0"
  },
  {
    "GroupId": "sg-0123456789abcdef0",
    "GroupName": "test",
    "Direction": "ingress",
    "Protocol": "tcp",
    "FromPort": 0,
    "ToPort": 100,
    "PeerType": "ipv6",
    "Peer": "::/0"
  },
  {
    "GroupId": "sg-0123456789abcdef0",
    "GroupName": "test",
    "Direction": "ingress",
    "Protocol": "-1",
    "FromPort": null,
    "ToPort": null,
    "PeerType": "ipv6",
    "Peer": "::/0"
  },
  {
    "GroupId": "sg-0123456789abcdef0",
    "GroupName": "test",
    "Direction": "ingress",
    "Protocol": "-1",
    "FromPort": null,
    "ToPort": null,
    "PeerType": "group",
    "Peer": "sg-0123456789abcdef1"
  },
  {
    "GroupId": "sg-0123456789abcdef0",
    "GroupName": "test",
    "Direction": "ingress",
    "Protocol": "udp",
    "FromPort": 22,
    "ToPort": 22,
    "PeerType": "ipv4",
    "Peer": "192.0.2.1/32"
  },
  {
    "GroupId": "sg-0123456789abcdef0",
    "GroupName": "test",
    "Direction": "egress",
    "Protocol": "-1",
    "FromPort": null,
    "ToPort": null,
    "PeerType": "ipv4",
    "Peer": "0.0.0.0/0"
  }
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws sg-rules [-h] [--profile PROFILE] [--region REGION]
                    [--endpoint-url ENDPOINT_URL] [--ca-bundle CA_BUNDLE]
                    [--output {json,text,table}]
                    group_id
```

## get-group-id

Resolve one exact group name inside a specified VPC.

Requires group name followed by VPC ID. Returns one JSON string. Zero or multiple matches fail with exit 1. Quoted names remain literal filter values.

```sh
aws get-group-id test vpc-0123456789abcdef0 --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
"sg-0123456789abcdef0"
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws get-group-id [-h] [--profile PROFILE] [--region REGION]
                        [--endpoint-url ENDPOINT_URL] [--ca-bundle CA_BUNDLE]
                        [--output {json,text,table}]
                        group_name vpc_id
```

## public-ports

Find ingress peers open to every IPv4 or IPv6 address.

Checks ingress peers equal to `0.0.0.0/0` or `::/0`. Preserves protocol and full port range in each row. More-specific publicly routable CIDRs fall outside this report. Internet reachability also depends on routing, network ACLs, and other controls.

```sh
aws public-ports --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  {
    "GroupId": "sg-0123456789abcdef0",
    "GroupName": "test",
    "Direction": "ingress",
    "Protocol": "tcp",
    "FromPort": 0,
    "ToPort": 100,
    "PeerType": "ipv4",
    "Peer": "0.0.0.0/0"
  },
  {
    "GroupId": "sg-0123456789abcdef0",
    "GroupName": "test",
    "Direction": "ingress",
    "Protocol": "tcp",
    "FromPort": 0,
    "ToPort": 100,
    "PeerType": "ipv6",
    "Peer": "::/0"
  },
  {
    "GroupId": "sg-0123456789abcdef0",
    "GroupName": "test",
    "Direction": "ingress",
    "Protocol": "-1",
    "FromPort": null,
    "ToPort": null,
    "PeerType": "ipv6",
    "Peer": "::/0"
  }
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws public-ports [-h] [--profile PROFILE] [--region REGION]
                        [--endpoint-url ENDPOINT_URL] [--ca-bundle CA_BUNDLE]
                        [--output {json,text,table}]
```

## allow-my-ip

Add one ingress rule for a single IPv4 or IPv6 host.

Changes AWS resources. Arguments: group ID, `tcp|udp`, port or ordered `START-END` range, optional host CIDR. Requires explicit profile and region arguments. CIDR must be IPv4 `/32` or IPv6 `/128`; omission looks up the current public IPv4 over HTTPS. Resolves STS identity before changing the exact rule. A duplicate grant returns `Changed: false` with reason `InvalidPermission.Duplicate`; other AWS failures remain visible.

```sh
aws allow-my-ip sg-0123456789abcdef0 tcp 22 192.0.2.1/32 --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
{
  "Return": true
}
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws allow-my-ip [-h] [--profile PROFILE] [--region REGION]
                       [--endpoint-url ENDPOINT_URL] [--ca-bundle CA_BUNDLE]
                       [--output {json,text,table}]
                       group_id {tcp,udp} port [cidr]
```

Example of an existing identical rule:

```json
{"Changed": false, "Reason": "InvalidPermission.Duplicate"}
```

## revoke-my-ip

Remove the matching single-host ingress rule.

Changes AWS resources. Uses the same arguments as `allow-my-ip`. Reuse the original protocol, range, and CIDR to remove the intended rule, especially if your public IP changed. An absent rule returns `Changed: false` with reason `InvalidPermission.NotFound`.

```sh
aws revoke-my-ip sg-0123456789abcdef0 udp 50-100 2001:db8::1/128 --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
{
  "Return": true
}
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws revoke-my-ip [-h] [--profile PROFILE] [--region REGION]
                        [--endpoint-url ENDPOINT_URL] [--ca-bundle CA_BUNDLE]
                        [--output {json,text,table}]
                        group_id {tcp,udp} port [cidr]
```

Example of an already absent rule:

```json
{"Changed": false, "Reason": "InvalidPermission.NotFound"}
```

## find-ssh-open

Find ingress rules permitting TCP port 22 or all protocols.

Includes ranges containing 22 and protocol `-1`. Returns every IPv4, IPv6, group, and prefix-list peer for those rules, including restricted peers. Inspect `Peer` to determine exposure. UDP-only port 22 rules are omitted.

```sh
aws find-ssh-open --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  {
    "GroupId": "sg-0123456789abcdef0",
    "GroupName": "test",
    "Direction": "ingress",
    "Protocol": "tcp",
    "FromPort": 0,
    "ToPort": 100,
    "PeerType": "ipv4",
    "Peer": "0.0.0.0/0"
  },
  {
    "GroupId": "sg-0123456789abcdef0",
    "GroupName": "test",
    "Direction": "ingress",
    "Protocol": "tcp",
    "FromPort": 0,
    "ToPort": 100,
    "PeerType": "ipv6",
    "Peer": "::/0"
  },
  {
    "GroupId": "sg-0123456789abcdef0",
    "GroupName": "test",
    "Direction": "ingress",
    "Protocol": "-1",
    "FromPort": null,
    "ToPort": null,
    "PeerType": "ipv6",
    "Peer": "::/0"
  },
  {
    "GroupId": "sg-0123456789abcdef0",
    "GroupName": "test",
    "Direction": "ingress",
    "Protocol": "-1",
    "FromPort": null,
    "ToPort": null,
    "PeerType": "group",
    "Peer": "sg-0123456789abcdef1"
  }
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws find-ssh-open [-h] [--profile PROFILE] [--region REGION]
                         [--endpoint-url ENDPOINT_URL] [--ca-bundle CA_BUNDLE]
                         [--output {json,text,table}]
```

For a report limited to rules open to everyone, inspect `public-ports` and select TCP ranges containing 22 or all-protocol rules.

