# Retired compatibility commands

These 13 names return exit 2 with migration guidance before invoking AWS. They remain for this compatibility release and are scheduled for removal in the next tagged release.

[Documentation index](README.md) · [Migration contracts](migration.md#retired-workflows)

## sg

Use aws ec2 with an explicit operation.

```sh
aws sg
```

```text
ERROR: sg is retired. Use aws ec2 with an explicit operation.
```

## install

Run python3 aws_alias_manager.py install from a clean checkout.

```sh
aws install
```

```text
ERROR: install is retired. Run python3 aws_alias_manager.py install from a clean checkout.
```

## rotate-iam-keys

Use your separately reviewed IAM key-rotation procedure.

```sh
aws rotate-iam-keys
```

```text
ERROR: rotate-iam-keys is retired. Use your separately reviewed IAM key-rotation procedure.
```

## iam-keys-days-remaining

Use an explicit per-key age and rotation-policy report.

```sh
aws iam-keys-days-remaining
```

```text
ERROR: iam-keys-days-remaining is retired. Use an explicit per-key age and rotation-policy report.
```

## create-assume-role

Define the role and trust policy in reviewed infrastructure code.

```sh
aws create-assume-role
```

```text
ERROR: create-assume-role is retired. Define the role and trust policy in reviewed infrastructure code.
```

## delete-virtual-mfa

Use an administrator MFA deactivation/deletion procedure.

```sh
aws delete-virtual-mfa
```

```text
ERROR: delete-virtual-mfa is retired. Use an administrator MFA deactivation/deletion procedure.
```

## authorize-my-ip-by-name

Use allow-my-ip with an explicit group ID, protocol and port.

```sh
aws authorize-my-ip-by-name
```

```text
ERROR: authorize-my-ip-by-name is retired. Use allow-my-ip with an explicit group ID, protocol and port.
```

## allow-my-ip-all

Use allow-my-ip with an explicit group ID, protocol and port.

```sh
aws allow-my-ip-all
```

```text
ERROR: allow-my-ip-all is retired. Use allow-my-ip with an explicit group ID, protocol and port.
```

## revoke-my-ip-all

Use revoke-my-ip with an explicit group ID, protocol and port.

```sh
aws revoke-my-ip-all
```

```text
ERROR: revoke-my-ip-all is retired. Use revoke-my-ip with an explicit group ID, protocol and port.
```

## assume

Configure a role profile and select it with --profile.

```sh
aws assume
```

```text
ERROR: assume is retired. Configure a role profile and select it with --profile.
```

## generate-sts-token

Use supported AWS profile providers or configure mfa-login.

```sh
aws generate-sts-token
```

```text
ERROR: generate-sts-token is retired. Use supported AWS profile providers or configure mfa-login.
```

## region

Use configure get region or configure set region with an explicit profile.

```sh
aws region
```

```text
ERROR: region is retired. Use configure get region or configure set region with an explicit profile.
```

## delete-ami

Use ami-snapshots <ami-id> to list the associated snapshots.

```sh
aws delete-ami
```

```text
ERROR: delete-ami is retired. Use ami-snapshots <ami-id> to list the associated snapshots.
```

