# Opinion publishing

Use `scripts/publish-opinions.sh` to publish second-agent opinion files into
`opinions/`.

```bash
scripts/publish-opinions.sh /path/to/opinions --dry-run
scripts/publish-opinions.sh /path/to/opinions
```

The script only accepts top-level `*.json` files from the source directory,
validates each file with `jq`, and writes only to `opinions/<filename>` through
the GitHub git data API.

Permission model:
- Prefer approving only `gh api` network access.
- Do not approve broad shell or Python network access for this task.
