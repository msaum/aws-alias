# Installation, upgrades, and recovery

[Documentation index](README.md) · [Getting started](getting-started.md)

Examples below use illustrative output. Paths containing `$HOME` or `~` describe portable install locations. SHA values made entirely of `a` or `b` are placeholders, and must be replaced with a real full commit SHA from this repository.

## Bootstrap

From a clean checkout, run:

```sh
python3 aws_alias_manager.py install
```

The manager checks the active AWS CLI version, validates the complete bundle, and records the checkout commit. If a personal alias file exists, it displays a diff and stops with exit 3. Review and preserve any custom entries before using:

```sh
python3 aws_alias_manager.py install --replace-local
```

The original alias file is backed up before activation. Installation and alias updates preserve AWS configuration and credential files. The retired `aws install` alias points callers to this bootstrap procedure.

Installed layout:

```text
~/.aws/cli/
  alias -> aws-alias/current/alias
  aws-alias/
    current -> bundles/<commit>-<unique-suffix>
    bundles/
      <commit>-<unique-suffix>/
        alias
        aws_alias_manager.py
        bundle.json
        installed.json
    backups/
      <timestamp>-<unique-suffix>/
        ... preserved alias file or bundle ...
```

`bundle.json` checks the distributed file contents. `installed.json` records the commit, installation time, original checksums, and previous managed version. File and directory types are checked to reject unexpected links. The source manifest shares the repository's trust boundary with the source code.

## upgrade

Update the active AWS CLI installation:

```sh
aws upgrade --dry-run
aws upgrade
```

`--dry-run` detects the provider and checks the supported update command, then prints the plan without executing the update. Illustrative output for a user-owned official installation:

```text
Active CLI: <path-to-active-aws>
Version: 2.37.7
Method: official
Action: <path-to-active-aws> update
```

Provider behavior:

| Installation | Action |
| --- | --- |
| Recognized Homebrew installation on macOS | Run `brew update`, then `brew upgrade awscli`. A pinned installation stops for explicit unpinning. |
| Recognized official macOS/Linux installation | Use its native `aws update` command. Root-owned installs require interactive sudo. |
| Unknown installation provider | Stop and direct the user to that provider's supported procedure. |

The manager verifies the active CLI path and version after the update. It rejects a downgraded version, an unexpected path, or a version below 2.37.7. An older CLI needs a one-time provider upgrade before bootstrap; consult [AWS installation guidance](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

To update both the CLI and aliases:

```sh
aws upgrade --all
aws upgrade --all --dry-run
```

The CLI update completes and is verified before the alias update begins. If the second step fails, the message identifies the completed CLI update and failed alias update. This sequence has no combined rollback.

## update-aliases

The manager resolves the default `main` branch to one commit and downloads the complete bundle from that commit. It validates download hosts, bounded reads, Python/shell/INI structure, supported targets, and checksums before activation.

Inspect an available version:

```sh
aws update-aliases --check
```

Illustrative output:

```text
Installed: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
Available: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
```

A content diff can follow. `--check` downloads and validates the candidate without activating it; local changes can still produce exit 3.

Apply an update:

```sh
aws update-aliases
```

The manager takes a lock, preserves the current bundle in a timestamped backup, stages the candidate, checks for concurrent edits, and atomically switches `current`. Repeating an update to the same unmodified version prints:

```text
The installed bundle is current.
```

Pin a reviewed version:

```sh
aws update-aliases --ref FULL_COMMIT_SHA
```

Replace `FULL_COMMIT_SHA` with the actual 40-character hexadecimal commit ID. Branch names such as `main`, short SHAs, and tags are rejected by `--ref`.

When installed files have local changes, updates stop with a diff. Preserve your edits, review the replacement, and then explicitly select the reviewed commit:

```sh
aws update-aliases --replace-local --ref FULL_COMMIT_SHA
```

Both flags are required for explicit replacement. This choice overwrites managed local edits after backing up the current version. A replaced alias symlink requires manual restoration of the expected layout; forced bundle replacement cannot repair it automatically.

## Roll back a managed update

```sh
aws update-aliases --rollback
```

Rollback requires a prior managed bundle whose files still match their recorded checksums. An initial bootstrap has no earlier managed version, even when a personal alias file was backed up. Current local changes remain protected; preserve them before choosing an explicit replacement pinned to the target version.

If the alias command is damaged, use the installed companion directly:

```sh
python3 "$HOME/.aws/cli/aws-alias/current/aws_alias_manager.py" aliases --rollback
```

If the companion itself is damaged, run the same `aliases --rollback` subcommand from a clean repository checkout. The companion exposes `install`, `upgrade`, `aliases`, and `run NAME` subcommands; `aliases` corresponds to `aws update-aliases`.

## Recover the original personal alias file

Find the bootstrap backup under `~/.aws/cli/aws-alias/backups`. Inspect its `personal-alias` file and any subsequent managed edits before restoring it. Copying a backup directly onto the installed alias symlink can change a managed version's contents. Preserve the current link and restore the original file through a separately reviewed filesystem operation. The manager retains the backup for that review.

## Developer tools

These tools operate on repository source and synthetic fixtures:

| Tool | Usage and purpose |
| --- | --- |
| `scripts/check_aliases.py` | `python3 scripts/check_aliases.py` checks inventory, supported references, migration coverage, profile/SSO coverage, and bundle integrity. Add `--aws-models` for offline native operation checks and `--shellcheck` for shell-body linting. |
| Manifest refresh | `python3 scripts/check_aliases.py --write-manifest` writes checksums for the distributed alias and companion. Review and commit them with the source change. |
| `scripts/install_ci_cli.py` | `python3 scripts/install_ci_cli.py 2.37.7` or `current` downloads and verifies an official CLI for CI. It invokes an installer and is intended for disposable runners. |
| Python contract suite | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s test -v` uses isolated homes, command doubles, and local service fixtures. Loopback access is needed for all tests to run without skips. |
| Bats entry checks | `bats test/no-valid-profile.bats` checks shell entry behavior in isolated environments. |
| CI | The workflow tests macOS/Linux, x86_64/arm64, and minimum/current CLI versions. |

All distribution files must come from the same reviewed commit. The [modernization record](modernization.md) documents the changes and validation scope.
