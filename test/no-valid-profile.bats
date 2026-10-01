#!/usr/bin/env bats
# Small shell entry-point checks. The full contract suite uses unittest.
setup() {
  task_root="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  task_python="$(command -v python3)"
  mkdir -p "$BATS_TEST_TMPDIR/home"
}

@test "tostring reads the fixture without AWS configuration" {
  run env -i HOME="$BATS_TEST_TMPDIR/home" PATH="$(dirname "$task_python"):/usr/bin:/bin" \
    "$task_python" "$task_root/aws_alias_manager.py" run tostring "$task_root/test/tostring.json"
  [ "$status" -eq 0 ]
  [ "$output" = '"{\"StreamNames\":[]}"' ]
}

@test "retired key rotation stops before any AWS command" {
  run env -i HOME="$BATS_TEST_TMPDIR/home" PATH="$(dirname "$task_python"):/usr/bin:/bin" \
    "$task_python" "$task_root/aws_alias_manager.py" run rotate-iam-keys
  [ "$status" -eq 2 ]
  [[ "$output" == *"retired"* ]]
}
