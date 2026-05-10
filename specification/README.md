# Clockodo OpenAPI specification

`openapi.yaml` is a vendored copy of the Clockodo REST API specification. It
exists for offline reference, schema-drift detection, and to make upstream
changes diffable from this repo.

**Do not hand-edit.** Refresh from upstream instead.

## Source

`https://docs.clockodo.com/openapi.yaml`

## Refresh procedure

```bash
curl -sSL -o specification/openapi.yaml https://docs.clockodo.com/openapi.yaml
```

Then verify the version line and commit:

```bash
grep -m1 "^  version:" specification/openapi.yaml
```

The spec's `info.version` field is an ISO date (e.g. `2026-05-06`) — use that
as the reference point in commit messages.
