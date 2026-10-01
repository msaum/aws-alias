# Local JSON and public-IP utilities

All examples use synthetic fixtures and illustrative identifiers. Account IDs, profile names, resource IDs, IPs, and hostnames identify no live resources. JSON/text/table examples were captured through the implementation using command doubles or a localhost service, with placeholder normalization for readability. Prompts and provider-specific messages are illustrative. Replace example arguments with your own values before running commands.

[Documentation index](README.md) · [Account and region selection](getting-started.md#select-a-profile-and-region)

These commands operate without AWS account credentials. The public-IP lookup requires internet access.

## Commands

[tostring](#tostring) · [my-ip](#my-ip)

## tostring

Encode a local JSON document as one JSON string.

Requires a JSON file path. Parses the document, creates compact JSON, and serializes that text as a JSON string. Reads a local file and requires no AWS profile. Invalid JSON or an unreadable file fails.

Create the example file first:

```sh
printf '%s\n' '{"enabled":true,"items":[1,2]}' > example.json
```

```sh
aws tostring example.json
```

Synthetic example output:

```json
"{\"enabled\":true,\"items\":[1,2]}"
```

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws tostring [-h] [--profile PROFILE] [--region REGION]
                    [--endpoint-url ENDPOINT_URL] [--ca-bundle CA_BUNDLE]
                    [--output {json,text,table}]
                    file
```

## my-ip

Look up the current public IPv4 address.

Makes an HTTPS request to `checkip.amazonaws.com` and validates its IPv4 response. Requires internet access and no AWS profile. Prints one plain-text address. NAT or a proxy can determine the observed address.

```sh
aws my-ip
```

Illustrative output:

```text
203.0.113.8
```

Companion parser syntax (use `--aws-` options in an alias invocation, or normal options after `--`):

```text
usage: aws my-ip [-h] [--profile PROFILE] [--region REGION]
                 [--endpoint-url ENDPOINT_URL] [--ca-bundle CA_BUNDLE]
                 [--output {json,text,table}]
```
