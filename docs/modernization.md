# AWS CLI alias modernization

Review and implementation date: October 1, 2026.

The review covered 74 original aliases. The implementation adds `ami-snapshots`, bringing the inventory to 75, and retains `upgrade` and `update-aliases` through a companion manager. Thirteen compatibility entries report migration guidance and exit before making AWS requests.

## Findings and changes

| Finding | Implemented change | Evidence in test/test_contracts.py |
| --- | --- | --- |
| F01: AWS context | Simple commands use native aliases. Helpers accept explicit prefixed flags and separator flags, require profile selection, and forward context to every AWS subprocess. | ActualAliasTests.test_helper_flags_separator_spaces_and_native_global_consumption; WorkflowTests.test_profiles_regions_and_endpoints_are_forwarded; LocalEndpointTests |
| F02: test isolation | Temporary HOME with spaces; dedicated empty/dummy config and credentials; allowlisted environment; metadata disabled; strict command doubles; local HTTP fixtures. | IsolatedCase; WorkflowTests; LocalEndpointTests; test/no-valid-profile.bats |
| F03: unsafe update | Entire bundle pinned to a SHA; validated downloads; protected local edits; lock; backups; atomic switch; direct recovery and rollback. | BundleTests, including transfer, validation, backup, activation and concurrent-edit failures |
| F04: ECR password | get-login-password followed by Docker --password-stdin, with explicit registry/account context. | WorkflowTests.test_ecr_password_only_on_stdin_and_region_validation |
| F05: invalid targets | sg compatibility error; EC2 volume operation; corrected companion operations; native command-model checks. | NativeModelTests; WorkflowTests.test_every_aws_workflow_success_and_failure; scripts/check_aliases.py |
| F06: SG helpers | Scoped group/protocol/port/host-CIDR validation; exact rule changes; legacy broad helpers retired; contextual lookup before writes. | WorkflowTests.test_no_mutation_with_invalid_security_group_arguments; test_public_and_ssh_rule_scope; test_permission_idempotence_and_denied_mutation |
| F07: failure status | Checked subprocesses; distinct usage/local-conflict statuses; successful empty results; partial region errors; denied requests remain visible. | WorkflowTests success/failure/empty cases; LocalEndpointTests native success/empty/failure and second-page denial |
| F08: JSON transforms | Internal JSON requests; safe argument arrays; standard-library JSON; literal local search; nullable tag handling. | WorkflowTests.test_ambient_output_does_not_change_json_transforms; test_empty_responses_and_missing_tags; test_profiles_regions_and_endpoints_are_forwarded |
| F09: report accuracy | Fixed CSV headers; InstanceId repair; MFA device enumeration; multiple VPC IDs; INFORMATIONAL severity; basic/enhanced ECR findings; per-resource Security Hub CSV. | WorkflowTests.test_csv_round_trips_and_fields; test_securityhub_counts_ignore_metadata; test_scan_status_and_basic_enhanced_findings; LocalEndpointTests |
| F10: credential workflows | Downloaded rotation dependency and credential-writing helpers retired; native configure mfa-login; configured profile migration documented. | WorkflowTests.test_retired_entries_do_not_invoke_aws; ActualAliasTests; NativeModelTests |
| F11: portability | POSIX entry bodies; Python 3.11+ stdlib; portable temporary directories; updater ownership checks; macOS/Linux architecture matrix. | UpgradeTests; BundleTests; .github/workflows/test.yml |
| F12: names and docs | Read-only ami-snapshots; actual PrivateDnsName; assigned-MFA contract; logs tail 10m; every original alias mapped; historical dead comments removed. | docs/migration.md; docs/alias-dispositions.json; WorkflowTests; alias inventory check |

## Validation

The final 52-test suite passed locally on macOS arm64 with AWS CLI 2.37.7. All 16 push and pull-request CI checks passed across macOS and Linux, x86_64 and arm64, with minimum and current CLI versions. Static checks covered the alias inventory, command models, bundle checksums, migration dispositions, and profile/SSO contracts. Both Bats tests and ShellCheck passed.

Tests use temporary homes, strict command doubles, and local HTTP fixtures. The real AWS CLI exercised native alias parsing, SSO credential resolution, role chaining, pagination, expired sessions, and service errors. Automated tests simulate installation, upgrades, Docker authentication, and AWS resource changes. Live service permissions and customer workflows require separate checks.

## Installation and updates

Python 3.11+ and AWS CLI 2.37.7+ are required. Install the alias file, companion manager, and manifest from one commit. Updates resolve the default main branch to a commit, validate the whole bundle, preserve backups, protect local edits, and switch the active bundle atomically. A full commit SHA can pin an update. Helper commands accept `--aws-profile` and `--aws-region`, or normal AWS flags after `--`; native aliases accept ordinary AWS global flags.

## Records

[Migration contracts](migration.md) describe every original alias and output schema. The [disposition inventory](alias-dispositions.json) records approved actions; the [implementation checklist](implementation-checklist.md) links findings to tests. [Profile and SSO contracts](profiles-and-sso.md) cover all current entries.

This Markdown record replaces the local HTML review. Host identifiers, personal AWS profiles, account details, and local paths have been removed. The Apache license remains in the repository.
