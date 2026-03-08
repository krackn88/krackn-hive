---
name: github-mcp
description: Use the GitHub MCP to search repos, fetch file contents, create PRs/issues, and push code. Use when pulling patterns from GitHub, searching for reference implementations, or managing GitHub workflow.
---

# GitHub MCP Usage

Available tools (server: `user-github`):

- **search_repositories** – `query`, optional `page`, `perPage`
- **get_file_contents** – `owner`, `repo`, `path`, optional `branch`
- **create_pull_request**, **list_pull_requests**, **merge_pull_request**
- **create_issue**, **list_issues**, **search_issues**
- **create_branch**, **push_files**, **create_or_update_file**

Token is configured in `~/.cursor/mcp.json`. Restart Cursor after changing it. If auth fails, revoke the token at https://github.com/settings/tokens and create a new one.
