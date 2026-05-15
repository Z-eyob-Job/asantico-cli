# MCP Integration Check (Lab 2.4 evidence)

Configured a GitHub MCP server in `.mcp.json` and demonstrated successful tool calls from Claude Code v2.1.12.

## Configuration

`.mcp.json` at repo root:

    {
      "mcpServers": {
        "github": {
          "type": "http",
          "url": "https://api.githubcopilot.com/mcp/",
          "headers": {
            "Authorization": "Bearer ${GITHUB_TOKEN}"
          }
        }
      }
    }

The token is read from the `GITHUB_TOKEN` environment variable at runtime; no secret is committed.

## Connection verification

In Claude Code:

    /mcp

Output:

    Manage MCP servers
    1 server

      Project MCPs (/Users/extra/Documents/AI410/Sprint 1/asantico-cli/.mcp.json)
    > github . connected

## Live tool call transcript

Prompt sent to Claude Code:

    Using the GitHub MCP server, perform two tool calls and show me the raw results:
    1. Fetch the most recent commits on Z-eyob-Job/asantico-cli (main branch).
       Show me the SHA, commit message, and author of the top 3 commits.
    2. Get the repository metadata: default branch, visibility, created_at timestamp.

Claude Code response (abridged):

    github - List commits (MCP)(owner: "Z-eyob-Job", repo: "asantico-cli", sha: "main", perPage: 3)
    [
      {
        "sha": "aa05489aab3d0abd204f8f0130f5afaeaad4e822",
        ...
      }
    ]

    github - Get file or directory contents (MCP)(owner: "Z-eyob-Job", repo: "asantico-cli", path: "/")
    [...directory listing returned...]

    github - Search repositories (MCP)(query: "repo:Z-eyob-Job/asantico-cli", minimal_output: false)
    {
      "total_count": 1,
      ...
    }

## Verified results

Most recent commits (main branch):

| SHA (short) | Commit message | Author |
|---|---|---|
| aa05489 | merge: Sprint 1 deliverable (spec-driven CLI) | Z-eyob-Job |
| 03da335 | docs(prompt-log): finalize with implementation summary and metrics | Z-eyob-Job |
| ef92086 | docs(readme): write project README with quick start and rubric mapping | Z-eyob-Job |

Repository metadata:

| Property | Value |
|---|---|
| Default branch | main |
| Visibility | public |
| Created at | 2026-05-15T18:55:01Z |

## Conclusion

The GitHub MCP integration is operational. Claude Code is able to invoke MCP tools (list_commits, get_file_contents, search_repositories) and receive structured responses from the upstream MCP server, satisfying Lab 2.4: "Connect at least one MCP server and demonstrate one successful tool call from Claude Code."
