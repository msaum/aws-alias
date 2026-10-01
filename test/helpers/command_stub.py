#!/usr/bin/env python3
"""Strict scripted command double. Every invocation must match the next step."""
import json
import os
from pathlib import Path
import sys

program, *args = sys.argv[1:]
script = json.loads(Path(os.environ['COMMAND_SCRIPT']).read_text())
log = Path(os.environ['COMMAND_LOG'])
previous = log.read_text().splitlines() if log.exists() else []
stdin = sys.stdin.read() if script.get('read_stdin_program') == program else None
with log.open('a') as stream:
    stream.write(json.dumps({'program': program, 'argv': args, 'stdin': stdin}) + '\n')
try:
    step = script['steps'][len(previous)]
except IndexError:
    print(f'Unexpected {program} invocation: {args}', file=sys.stderr)
    sys.exit(97)
if program != step.get('program', 'aws') or args[:len(step['prefix'])] != step['prefix']:
    print(f'Unexpected {program} invocation: {args}; expected {step}', file=sys.stderr)
    sys.exit(97)
for flag, expected in step.get('options', {}).items():
    if flag not in args or args[args.index(flag) + 1] != expected:
        print(f'Wrong option {flag}: {args}', file=sys.stderr)
        sys.exit(98)
if 'json' in step:
    print(json.dumps(step['json']))
else:
    print(step.get('stdout', ''), end='')
if step.get('stderr'):
    print(step['stderr'], file=sys.stderr)
sys.exit(step.get('code', 0))
