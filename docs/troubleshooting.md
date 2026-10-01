# Troubleshooting

[Documentation index](README.md) · [Getting started](getting-started.md)

## whoami fails while direct STS succeeds

The current entry is native:

```ini
whoami = sts get-caller-identity
```

A historical shell wrapper discarded profile flags and replaced STS errors with a generic credential message. Check the active alias file at `~/.aws/cli/alias`. Install or update the complete managed bundle after reviewing the diff. Verify the same selected profile:

```sh
aws sts get-caller-identity --profile example-sso
aws --profile example-sso whoami
```

## A helper selected the wrong profile

Use `--aws-profile example-sso`, or place `--profile example-sso` after `--`. Ordinary outer AWS global flags are consumed before shell alias execution. Inspect the helper's `Scope:` message on stderr.

```sh
aws find-ssh-open --aws-profile example-sso --aws-region us-east-1
aws find-ssh-open -- --profile example-sso --region us-east-1
```

Grant/revoke and ECR login require explicit profile and region arguments. Ambient environment values alone are insufficient for those commands.

## An SSO session is missing or expired

```sh
aws sso login --profile example-sso
aws whoami --profile example-sso
```

The native provider supplies login guidance. Credential resolution and IAM service permissions are separate steps; an authenticated role can still receive AccessDenied for an inventory API.

## list-virtual-mfa requires a username

Supply the IAM user whose assigned devices you want to inspect:

```sh
aws list-virtual-mfa demo-user --aws-profile example-sso
```

The command calls the IAM assigned-device API. SSO identity-provider MFA is administered through IAM Identity Center and the identity provider.

## Output is empty

An empty inventory normally succeeds. JSON helpers emit `[]`, text/table helpers can print nothing, and CSV helpers print their header. Check profile, region, filters, and permissions. Some commands have stricter lookup contracts: `get-group-id` requires exactly one match, and a non-ready image scan returns a failure status.

## CSV has more lines than records

Quoted fields can include newlines. Security Hub also expands one finding into a row for each resource. Parse CSV with a CSV reader and count logical records. Keep stderr separate from report files.

## A region inventory is incomplete

`list-instances` attempts every selected region, emits completed data, and reports region failures with nonzero status. Treat that result as partial and review stderr before using it as a complete inventory. `all` discovers enabled regions for the selected account.

## A security-group rule did not change

`Changed: false` identifies a duplicate grant or an already absent revocation. Other errors retain their AWS failure. Revocation must match the original protocol, port range, and host CIDR. Use the saved original CIDR if your public IP changed. A host rule can still be blocked by other network controls.

## Alias update exits 3

Managed files or the active link differ from the recorded installation. Preserve those changes and review the displayed diff. Replacement needs `--replace-local --ref FULL_COMMIT_SHA`. A substituted alias link needs manual recovery of the expected path. See [maintenance and recovery](maintenance.md).

## Alias update exits 4

Another process holds the update lock. Let the active installation or update finish, then retry. Avoid running bootstrap, CLI update, and alias update concurrently.

## Installation or update cannot fetch the bundle

Check access to the configured GitHub repository, HTTPS connectivity, and the requested commit. The distributed updater uses unauthenticated HTTPS and expects publicly readable source. A private repository returns access errors. Invalid or incomplete downloads fail before activation.

## upgrade cannot identify the installation

Inspect the `aws` executable resolved by your shell and use that installation provider's update procedure. Homebrew-pinned packages require explicit unpinning. Official root-owned installations require an interactive sudo terminal. Use `aws upgrade --dry-run` to inspect the recognized plan.

## A command says it is retired

It returns exit 2 before making an AWS request. Follow the command's migration message and consult [retired commands](retired.md). Credential, key-rotation, role-creation, and MFA-removal procedures need their own reviewed administration workflow.
