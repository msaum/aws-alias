# Modernization implementation evidence

The source implements the approved scope for all 74 original aliases. `ami-snapshots` brings the distributed inventory to 75. `docs/alias-dispositions.json` records each original recommendation, its approved action, the result and the test family. The migration table provides the readable contract.

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

## Validation boundaries

The final 52-test suite and all 16 CI checks passed across the supported macOS/Linux architecture and CLI-version matrix. Both Bats tests and ShellCheck passed. See [the modernization record](modernization.md) for test scope and runtime boundaries.

## Release handling

Ship alias, aws_alias_manager.py and bundle.json from the same commit. The source bundle contains its file checksums; installed metadata records the chosen commit and original checksums. Repeated updates to the same unmodified bundle succeed without switching. A failed alias update after `upgrade --all` reports the completed CLI update separately.

Retired compatibility entries exit 2 in this release. Remove their aliases and messages in the next tagged release after applying the documented migration. Preserve the Apache license and upstream attribution. No automatic credential migration is part of bundle installation or updates.
