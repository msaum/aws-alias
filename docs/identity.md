# Profiles, identity, and IAM

All examples use synthetic fixtures and illustrative identifiers. Account IDs, profile names, resource IDs, IPs, and hostnames identify no live resources. JSON/text/table examples were captured through the implementation using command doubles or a localhost service, with placeholder normalization for readability. Prompts and provider-specific messages are illustrative. Replace example arguments with your own values before running commands.

[Documentation index](README.md) · [Account and region selection](getting-started.md#select-a-profile-and-region)

IAM reports require the selected role to allow the listed IAM operations. They inspect IAM users in that account. `profiles` reads local configuration; `mfa` writes a local session profile.

## Commands

[profiles](#profiles) · [mfa](#mfa) · [whoami](#whoami) · [find-access-key](#find-access-key) · [list-iam-users](#list-iam-users) · [list-user-keys](#list-user-keys) · [list-virtual-mfa](#list-virtual-mfa) · [find-users-without-mfa](#find-users-without-mfa)

## profiles

List configured profile names.

Expands to `configure list-profiles`. Reads local configuration and credential profiles. Listing a name does not validate its session or permissions.

```sh
aws profiles
```

Illustrative output:

```text
example-sso
example-iam
example-session
```

Native expansion:

```text
aws configure list-profiles
```

## mfa

Create temporary IAM-user credentials using an OTP MFA device.

Expands to `configure mfa-login`. Uses an IAM-user access key and virtual or hardware OTP MFA to request STS session credentials, then writes them to the chosen local profile. Use `--update-profile` to choose the destination. IAM Identity Center users log in with `aws sso login`. See [AWS mfa-login reference](https://docs.aws.amazon.com/cli/latest/reference/configure/mfa-login.html).

```sh
aws mfa --profile example-iam --update-profile example-session --duration-seconds 3600
```

Illustrative output:

```text
MFA token code: <enter the current OTP code>
Temporary credentials written to profile 'example-session'
```

Native expansion:

```text
aws configure mfa-login
```

## whoami

Return the identity used by the selected profile.

Expands to `sts get-caller-identity`. Returns `UserId`, `Account`, and `Arn`. Useful immediately after selecting a profile or logging in to SSO. Global `--profile`, `--region`, `--output`, and `--query` use native CLI behavior.

```sh
aws whoami --profile example-sso --region us-east-1 --output json
```

Synthetic example output:

```json
{
    "UserId": "fixture-user-id-0000",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/fixture"
}
```

Native expansion:

```text
aws sts get-caller-identity
```

## find-access-key

Find IAM users who own an access key ID.

Accepts a 20-character uppercase alphanumeric key ID. Enumerates IAM users and their key metadata. Returns matching usernames; an empty array means no match among those users. Temporary role keys and root keys fall outside this search. Any failed IAM request stops the scan.

```sh
aws find-access-key AAAAAAAAAAAAAAAAAAAA --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  "hardware-user"
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws find-access-key [-h] [--profile PROFILE] [--region REGION]
                           [--endpoint-url ENDPOINT_URL]
                           [--ca-bundle CA_BUNDLE]
                           [--output {json,text,table}]
                           key
```

## list-iam-users

List IAM usernames in the selected account.

Uses `iam list-users`, projects `UserName`, and displays a table. Requires IAM user-listing permission. Identity Center users are managed separately from IAM users.

```sh
aws list-iam-users --profile example-sso --region us-east-1
```

Synthetic example output:

```text
---------------
|  ListUsers  |
+-------------+
|  demo-user  |
+-------------+
```

Native expansion:

```text
aws iam list-users --query Users[].UserName --output table
```

## list-user-keys

List access-key metadata for an IAM user.

Requires a username. Calls `iam list-access-keys`; returns key ID, status, creation time, and username when supplied by AWS. It exposes metadata only and leaves keys unchanged.

```sh
aws list-user-keys hardware-user --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  {
    "AccessKeyId": "AAAAAAAAAAAAAAAAAAAA"
  }
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws list-user-keys [-h] [--profile PROFILE] [--region REGION]
                          [--endpoint-url ENDPOINT_URL]
                          [--ca-bundle CA_BUNDLE] [--output {json,text,table}]
                          username
```

## list-virtual-mfa

List MFA devices assigned to an IAM user.

Requires an explicit IAM username and calls `iam list-mfa-devices`. Includes hardware and virtual devices. The historical alias name remains for compatibility. It queries IAM device assignments in the selected account.

```sh
aws list-virtual-mfa hardware-user --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  {
    "UserName": "hardware-user",
    "SerialNumber": "hardware-serial",
    "EnableDate": "2026-01-01T00:00:00Z"
  }
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws list-virtual-mfa [-h] [--profile PROFILE] [--region REGION]
                            [--endpoint-url ENDPOINT_URL]
                            [--ca-bundle CA_BUNDLE]
                            [--output {json,text,table}]
                            username
```

## find-users-without-mfa

Find IAM users with zero assigned MFA devices.

Enumerates every IAM user and checks `iam list-mfa-devices` per user, including hardware devices. Returns usernames with no assignments. This is an assignment inventory; identity-provider MFA and authentication-policy enforcement require separate checks.

```sh
aws find-users-without-mfa --aws-profile example-sso --aws-region us-east-1
```

Synthetic example output:

```json
[
  "never-used"
]
```

The helper writes selected profile/region information to stderr; the block above shows stdout.

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws find-users-without-mfa [-h] [--profile PROFILE] [--region REGION]
                                  [--endpoint-url ENDPOINT_URL]
                                  [--ca-bundle CA_BUNDLE]
                                  [--output {json,text,table}]
```
