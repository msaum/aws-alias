# AWS CLI aliases

This collection provides 75 top-level aliases for AWS CLI 2.37.7 or newer. Python 3.11+ runs the companion workflows and bundle manager using the standard library. Supported hosts are macOS and Linux on x86_64 and arm64. Docker is required for `docker-ecr-login`.

Native aliases expand into AWS commands. Workflows use a managed companion at `~/.aws/cli/aws-alias/current/aws_alias_manager.py`. The alias file and companion switch together through one pointer.

## Install

Use a clean, committed checkout of this repository. The installation checks the active AWS CLI version and validates the bundle manifest.

```sh
git clone --branch main https://github.com/msaum/aws-alias.git
cd aws-alias
python3 aws_alias_manager.py install
```

An existing alias file triggers a diff and exit 3. After reviewing it, run `python3 aws_alias_manager.py install --replace-local`. The manager saves a timestamped backup before replacing the file with `~/.aws/cli/alias -> aws-alias/current/alias`. Personal entries need a separate migration into a maintained bundle; every managed file participates in the local-change check.

For an older CLI, complete the one-time upgrade through its installation provider first. See the [official installation instructions](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

## Select account and region

Native aliases accept ordinary AWS global flags in either position:

```sh
aws --profile work whoami --region us-east-1
aws running-instances --profile work --region us-east-1
```

The outer AWS parser consumes ordinary global flags when invoking shell aliases. Helper options have an `--aws-` prefix, or you can place ordinary options after `--`:

```sh
aws get-asg-instance-ips 'group with spaces' --aws-profile work --aws-region us-east-1
aws ami-snapshots ami-0123456789abcdef0 -- --profile work --region us-east-1
aws list-instances us-east-1 us-west-2 --aws-profile work
```

Helpers require a profile from their arguments, `AWS_PROFILE`, or `AWS_DEFAULT_PROFILE`. Region precedence is helper argument, `AWS_REGION`, `AWS_DEFAULT_REGION`, then the selected profile configuration. An outer `--profile` flag is consumed before helper execution; use the forms above to select the helper profile. Explicit helper arguments take precedence over environment values.

Supported helper options are `--aws-profile`, `--aws-region`, `--aws-endpoint-url`, `--aws-ca-bundle`, and `--aws-output json|text|table`. CSV helpers have fixed output schemas. Helpers fetch JSON for transformations independently of the user's configured output. Scope information goes to stderr. Inspect `python3 aws_alias_manager.py run NAME --help` for each workflow's arguments.

Security-group writes and ECR login require profile and region in the helper arguments. Grant/revoke also require a group ID, protocol, and port. The CIDR must identify one IPv4 or IPv6 host; omitting it requests the current public IPv4 address over HTTPS.

```sh
aws allow-my-ip sg-0123456789abcdef0 tcp 443 203.0.113.8/32 --aws-profile work --aws-region us-east-1
aws revoke-my-ip sg-0123456789abcdef0 tcp 443 203.0.113.8/32 --aws-profile work --aws-region us-east-1
aws docker-ecr-login 123456789012.dkr.ecr.us-east-1.amazonaws.com --aws-profile work --aws-region us-east-1
```

## Profiles and IAM Identity Center (SSO)

Native aliases and retained AWS workflows use AWS CLI credential providers. Both current `sso-session` profiles and legacy SSO profiles are supported, including role profiles whose `source_profile` uses SSO. Login stays in the AWS CLI:

```sh
aws sso login --profile example-sso
aws --profile example-sso whoami
aws whoami --profile example-sso
aws get-asg-instance-ips 'group with spaces' --aws-profile example-sso
```

`whoami` must be the native entry `whoami = sts get-caller-identity`. The historical shell wrapper discarded profile flags and replaced useful errors with a generic credential error. An installed file containing that wrapper needs a reviewed bundle update. Shell workflows still require the helper flag forms described above because the outer AWS parser consumes ordinary global flags. Use an explicit helper profile when selecting an account; combining an ambient profile with an ordinary outer `--profile` can leave the helper using the ambient account.

Missing/expired SSO sessions preserve the CLI's login guidance and fail before dependent service calls. An authenticated SSO role also needs permission for the requested API. IAM reports inspect IAM users in the account; `list-virtual-mfa` requires an explicit IAM username. `mfa` is the IAM-user OTP workflow. IAM Identity Center authentication uses `aws sso login` and the identity provider's MFA process.

[The complete profile/SSO audit](docs/profiles-and-sso.md) lists all 75 entries and their invocation contracts. The default branch is `main`. Alias updates follow it unless `--ref` pins a reviewed full commit SHA.

## Update and recover

```sh
aws upgrade --dry-run
aws upgrade
aws update-aliases --check
aws update-aliases
aws upgrade --all
aws update-aliases --rollback
```

`upgrade` updates the active CLI. On macOS, a proven Homebrew installation uses `brew update` and `brew upgrade awscli`; pinned installations stop. Official installations on macOS/Linux, identified through installer metadata or the versioned layout, use the CLI's native `aws update`, with interactive sudo when the installation is owned by root. Unknown installation providers require their own upgrade procedure. The manager checks the active path and resulting version. `--all` starts the alias update after CLI verification. A later alias failure reports that the CLI update already succeeded.

`update-aliases` resolves the repository's default branch to a commit SHA and downloads the whole bundle from that SHA. `--ref FULL_COMMIT_SHA` selects a specific revision. HTTPS transport, allowed download hosts, bounded reads, INI/shell/Python validation, and manifest checksums protect transfer integrity. The manifest comes from the same repository as the code; it provides integrity within that repository trust boundary.

Changed files stop an update with exit 3 and a diff. Explicit replacement requires both `--replace-local` and `--ref FULL_COMMIT_SHA`. Updates take a lock, save a timestamped backup, check for concurrent edits, stage a version directory, and atomically replace the `current` link. `--check` downloads and validates the candidate without activating it. `--rollback` restores the previous unmodified bundle. Files and backups stay available for recovery.

If an alias entry breaks, invoke the manager directly:

```sh
python3 "$HOME/.aws/cli/aws-alias/current/aws_alias_manager.py" aliases --rollback
```

If the current companion breaks, use a clean checkout's `python3 aws_alias_manager.py aliases --rollback`. A replaced alias symlink requires manual recovery after reviewing its contents. Backups live under `~/.aws/cli/aws-alias/backups`; each directory contains either the preserved personal alias or the prior complete bundle. Recovery can copy those files into a separately maintained checkout. The manager preserves credential files during installation and updates.

Success and empty results return 0. Usage errors return 2, local conflicts 3, and lock contention 4. AWS command failures preserve their nonzero status and stderr; other failures return 1. A region scan returns completed regions and a nonzero result when any selected region fails.

## Migration and checks

[Migration contracts](docs/migration.md) describe every original alias and each report schema. [Implementation evidence](docs/implementation-checklist.md) maps findings F01–F12 to code and tests. Thirteen retired names provide migration errors for this release and are scheduled for removal in the next tagged release.

Run the credential-free suite:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s test -v
python3 scripts/check_aliases.py --aws-models --shellcheck
bats test/no-valid-profile.bats
```

The model checks require AWS CLI; lint and shell checks require ShellCheck and Bats. Tests create temporary homes, dedicated config files, strict command doubles, and loopback endpoints with dummy credentials. CI covers minimum/current CLI versions on macOS and Linux, with x86_64 and arm64 runners. CI results and optional live sandbox tests remain separate evidence.

After changing a distributed file, refresh `bundle.json` with `python3 scripts/check_aliases.py --write-manifest` and commit the bundle together. The Apache 2.0 license remains in the repository. This project began as a fork of [maishsk/aws-alias](https://github.com/maishsk/aws-alias), created by [Maish Saidel-Keesing](https://github.com/maishsk). Credit goes to Maish for assembling the original AWS CLI alias collection. This repository starts from a reviewed modernization snapshot. Background: [AWS alias documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-alias.html), [original collection article](https://blog.technodrone.cloud/2021/02/aws-cli-aliases.html), and [AWS implementation](https://github.com/aws/aws-cli/blob/v2/awscli/alias.py).

The [modernization record](docs/modernization.md) summarizes the review, changes, and validation.
