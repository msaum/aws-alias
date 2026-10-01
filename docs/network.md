# Regions and network inventory

All examples use synthetic fixtures and illustrative identifiers. Account IDs, profile names, resource IDs, IPs, and hostnames identify no live resources. JSON/text/table examples were captured through the implementation using command doubles or a localhost service, with placeholder normalization for readability. Prompts and provider-specific messages are illustrative. Replace example arguments with your own values before running commands.

[Documentation index](README.md) · [Account and region selection](getting-started.md#select-a-profile-and-region)

These commands read EC2 metadata in the selected account and region, except region discovery which lists available regions. Table projections intentionally retain a compact set of fields.

## Commands

[list-all-regions](#list-all-regions) · [list-azs](#list-azs) · [vpc-peers](#vpc-peers) · [find-nat-gateway-by-public-ip](#find-nat-gateway-by-public-ip) · [list-igw](#list-igw) · [list-ngw](#list-ngw) · [list-vgw](#list-vgw) · [list-vpn-connection](#list-vpn-connection) · [list-instance-status](#list-instance-status) · [list-vpcs](#list-vpcs) · [list-subnets](#list-subnets) · [list-routes](#list-routes)

## list-all-regions

List region names returned by EC2 discovery.

Uses `ec2 describe-regions` with native AWS defaults. Output is text; the default API response includes regions enabled for the account. Run the expanded operation with `--all-regions` when you need opt-in regions too.

```sh
aws list-all-regions --profile example-sso --region us-east-1
```

Synthetic example output:

```text
us-east-1
```

Native expansion:

```text
aws ec2 describe-regions --query 'Regions[].RegionName' --output text
```

## list-azs

List availability-zone names for the selected region.

Uses `ec2 describe-availability-zones` and prints zone names as text. Account-specific zone names and availability follow the EC2 response.

```sh
aws list-azs --profile example-sso --region us-east-1
```

Synthetic example output:

```text
us-east-1a
```

Native expansion:

```text
aws ec2 describe-availability-zones --query 'AvailabilityZones[].ZoneName' --output text
```

## vpc-peers

List sorted Name-tag values of VPC peering connections.

Projects Name tags from `describe-vpc-peering-connections` and sorts them. Untagged connections contribute no name. The output contains names only; use the full service operation for IDs and status.

```sh
aws vpc-peers --profile example-sso --region us-east-1
```

Synthetic example output:

```text
demo-network
```

Native expansion:

```text
aws ec2 describe-vpc-peering-connections --query 'sort(VpcPeeringConnections[].Tags[?Key==`Name`].Value[]||`[]`)' --output text
```

## find-nat-gateway-by-public-ip

Find NAT gateways containing a public IP.

Requires an IP address. Fetches NAT gateways with CLI pagination and compares every returned address locally. Returns gateway IDs and nullable Name tags. This helper avoids relying on an unsupported API filter.

```sh
aws find-nat-gateway-by-public-ip 203.0.113.5 --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  {
    "NatGatewayId": "nat-0123456789abcdef0",
    "Name": null
  }
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws find-nat-gateway-by-public-ip [-h] [--profile PROFILE]
                                         [--region REGION]
                                         [--endpoint-url ENDPOINT_URL]
                                         [--ca-bundle CA_BUNDLE]
                                         [--output {json,text,table}]
                                         ip
```

## list-igw

Show internet gateways and their first attached VPC.

Table columns: `IGW`, `VpcId`, `Name`. The projection selects the first attachment; a gateway without attachments has a null VPC value.

```sh
aws list-igw --profile example-sso --region us-east-1
```

Synthetic example output:

```text
--------------------------------------------------------------------
|                     DescribeInternetGateways                     |
+------------------------+---------------+-------------------------+
|           IGW          |     Name      |          VpcId          |
+------------------------+---------------+-------------------------+
|  igw-0123456789abcdef0 |  demo-network |  vpc-0123456789abcdef0  |
|  igw-0123456789abcdef1 |  None         |  None                   |
+------------------------+---------------+-------------------------+
```

Native expansion:

```text
aws ec2 describe-internet-gateways  --query "InternetGateways[].{IGW:InternetGatewayId,VpcId: Attachments[].VpcId|[0], Name: Tags[?Key=='Name'].Value |[0] }"   --output table
```

## list-ngw

Show NAT gateways and their first address.

Table columns: `VpcId`, `NatGatewayId`, `SubnetId`, `PublicIp`, `PrivateIp`. Only the first address is projected. Use `ec2 describe-nat-gateways` for complete address inventories.

```sh
aws list-ngw --profile example-sso --region us-east-1
```

Synthetic example output:

```text
----------------------------------------------
|             DescribeNatGateways            |
+---------------+----------------------------+
|  NatGatewayId |  nat-0123456789abcdef0     |
|  PrivateIp    |  10.0.0.1                  |
|  PublicIp     |  203.0.113.1               |
|  SubnetId     |  subnet-0123456789abcdef0  |
|  VpcId        |  vpc-0123456789abcdef0     |
+---------------+----------------------------+
```

Native expansion:

```text
aws ec2 describe-nat-gateways  --query "NatGateways[].{VpcId:VpcId, NatGatewayId: NatGatewayId, SubnetId: SubnetId, PublicIp: NatGatewayAddresses[].PublicIp | [0], PrivateIp: NatGatewayAddresses[].PrivateIp | [0] }"  --output table
```

## list-vgw

Show VPN gateways and all attached VPC IDs.

Table columns: `VpnGatewayId`, `AmazonSideAsn`, `VpcIds`, `Name`. VPC IDs are sorted and joined with commas. An unattached gateway produces an empty `VpcIds` value.

```sh
aws list-vgw --profile example-sso --region us-east-1
```

Synthetic example output:

```text
---------------------------------------------------------------------------
|                           DescribeVpnGateways                           |
+---------------+---------------+--------------+--------------------------+
| AmazonSideAsn |     Name      |   VpcIds     |      VpnGatewayId        |
+---------------+---------------+--------------+--------------------------+
|  64512        |  demo-network |  vpc-a,vpc-b |  vgw-0123456789abcdef0   |
|  None         |  None         |              |  vgw-0123456789abcdef1   |
+---------------+---------------+--------------+--------------------------+
```

Native expansion:

```text
aws ec2 describe-vpn-gateways --query 'VpnGateways[].{VpnGatewayId:VpnGatewayId,AmazonSideAsn:AmazonSideAsn,VpcIds:join(`,`,sort(VpcAttachments[].VpcId||`[]`)),Name:Tags[?Key==`Name`].Value|[0]}' --output table
```

## list-vpn-connection

Show Site-to-Site VPN connections and gateway IDs.

Table columns: `VpnConnectionId`, `CustomerGatewayId`, `VpnGatewayId`, `Name`. This projection focuses on those identifiers; use `ec2 describe-vpn-connections` for tunnel telemetry and Transit Gateway fields.

```sh
aws list-vpn-connection --profile example-sso --region us-east-1
```

Synthetic example output:

```text
------------------------------------------------
|            DescribeVpnConnections            |
+--------------------+-------------------------+
|  CustomerGatewayId |  cgw-0123456789abcdef0  |
|  Name              |  demo-network           |
|  VpnConnectionId   |  vpn-0123456789abcdef0  |
|  VpnGatewayId      |  vgw-0123456789abcdef0  |
+--------------------+-------------------------+
```

Native expansion:

```text
aws ec2 describe-vpn-connections  --query "VpnConnections[].{ VpnConnectionId: VpnConnectionId, CustomerGatewayId:CustomerGatewayId,VpnGatewayId:VpnGatewayId, Name: Tags[?Key=='Name'].Value| [0] }"  --output table
```

## list-instance-status

Show EC2 state and system/instance status checks.

Table columns: `InstanceId`, `State`, `AZ`, `SystemStatus`, `InstanceStatus`. Native `describe-instance-status` defaults apply, normally returning running instances. Add `--include-all-instances` when querying other states.

```sh
aws list-instance-status --profile example-sso --region us-east-1
```

Synthetic example output:

```text
-------------------------------------------
|         DescribeInstanceStatus          |
+-----------------+-----------------------+
|  AZ             |  us-east-1a           |
|  InstanceId     |  i-0123456789abcdef0  |
|  InstanceStatus |  ok                   |
|  State          |  running              |
|  SystemStatus   |  ok                   |
+-----------------+-----------------------+
```

Native expansion:

```text
aws ec2 describe-instance-status  --query "InstanceStatuses[].{InstanceId: InstanceId, State: InstanceState.Name, AZ: AvailabilityZone, SystemStatus: SystemStatus.Status, InstanceStatus: InstanceStatus.Status}"  --output table
```

## list-vpcs

Show VPC IDs, IPv4 CIDRs, Name tags, and default status.

Table columns: `VpcId`, `CidrBlock`, `Name`, `IsDefault`. The projection shows the primary IPv4 CIDR; additional associations and IPv6 ranges require the full service response.

```sh
aws list-vpcs --profile example-sso --region us-east-1
```

Synthetic example output:

```text
-----------------------------------------------------------------------
|                            DescribeVpcs                             |
+-------------+------------+---------------+--------------------------+
|  CidrBlock  | IsDefault  |     Name      |          VpcId           |
+-------------+------------+---------------+--------------------------+
|  10.0.0.0/16|  False     |  demo-network |  vpc-0123456789abcdef0   |
|  None       |  None      |  None         |  vpc-0123456789abcdef1   |
+-------------+------------+---------------+--------------------------+
```

Native expansion:

```text
aws ec2 describe-vpcs  --query  "Vpcs[].{VpcId: VpcId, CidrBlock: CidrBlock,  Name: Tags[?Key=='Name'].Value| [0], IsDefault: IsDefault}"  --output table
```

## list-subnets

Show subnet location, parent VPC, and IPv4 CIDR.

Table columns: `AZ`, `VpcId`, `SubnetId`, `CidrBlock`, `Name`. Uses `ec2 describe-subnets`; absent tags remain null.

```sh
aws list-subnets --profile example-sso --region us-east-1
```

Synthetic example output:

```text
-------------------------------------------
|             DescribeSubnets             |
+------------+----------------------------+
|  AZ        |  us-east-1a                |
|  CidrBlock |  10.0.0.0/24               |
|  Name      |  demo-network              |
|  SubnetId  |  subnet-0123456789abcdef0  |
|  VpcId     |  vpc-0123456789abcdef0     |
+------------+----------------------------+
```

Native expansion:

```text
aws ec2 describe-subnets  --query "Subnets[].{AZ:AvailabilityZone,VpcId:VpcId,SubnetId:SubnetId,CidrBlock:CidrBlock,    Name: Tags[?Key=='Name'].Value| [0]}"  --output table
```

## list-routes

Show route-table IDs and IPv4 gateway projections.

Table columns include `RouteTableId`, `VpcId`, `Name`, and nested `GatewayId` rows with `GatewayId`/`DestinationCidrBlock`. NAT, Transit Gateway, interface, and IPv6 targets require the full `ec2 describe-route-tables` response. This compact view omits those fields.

```sh
aws list-routes --profile example-sso --region us-east-1
```

Synthetic example output:

```text
--------------------------------------------------------------------
|                        DescribeRouteTables                       |
+--------------+-------------------------+-------------------------+
|     Name     |      RouteTableId       |          VpcId          |
+--------------+-------------------------+-------------------------+
|  demo-network|  rtb-0123456789abcdef0  |  vpc-0123456789abcdef0  |
+--------------+-------------------------+-------------------------+
||                            GatewayId                           ||
|+------------------------------+---------------------------------+|
||     DestinationCidrBlock     |            GatewayId            ||
|+------------------------------+---------------------------------+|
||  0.0.0.0/0                   |  igw-0123456789abcdef0          ||
|+------------------------------+---------------------------------+|
```

Native expansion:

```text
aws ec2 describe-route-tables  --query "RouteTables[].{RouteTableId:RouteTableId, VpcId:VpcId, Name: Tags[?Key=='Name'].Value| [0], GatewayId: Routes[].{GatewayId:GatewayId,DestinationCidrBlock: DestinationCidrBlock} }  "  --output table
```

