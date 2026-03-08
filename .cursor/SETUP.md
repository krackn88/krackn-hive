# Cursor & GitHub MCP Setup

## GitHub Token Security (Important)

**If you shared your GitHub token in chat or elsewhere, revoke it immediately:**

1. Go to https://github.com/settings/tokens
2. Revoke the exposed token
3. Create a new token with the scopes you need (repo, read:org, etc.)
4. Update `~/.cursor/mcp.json` in the `github.env.GITHUB_PERSONAL_ACCESS_TOKEN` field
5. Restart Cursor for the MCP server to pick up the new token

## GitHub MCP

The GitHub MCP server is configured in `~/.cursor/mcp.json`. Available tools include:

- `search_repositories` - Search GitHub repos
- `get_file_contents` - Get file/dir contents from a repo
- `create_pull_request`, `list_pull_requests`, `merge_pull_request`
- `create_issue`, `list_issues`, `search_issues`
- `create_branch`, `push_files`, `create_or_update_file`

Restart Cursor after changing mcp.json.

## Project Rules and Skills

- **Rules** (`.cursor/rules/`): Python async, FastAPI, and krackn-hive patterns.
- **Skills** (`.cursor/skills/`): `krackn-hive-upgrade` (upgrade workflow), `github-mcp` (GitHub MCP usage).
- **AGENTS.md**: Project overview and conventions for AI agents.
