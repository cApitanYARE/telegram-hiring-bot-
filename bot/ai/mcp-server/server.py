import asyncio
from typing import Any
import httpx
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
import mcp.types as types
from mcp.server.stdio import stdio_server

server = Server("github-inspector")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name='analyze_user_repos',
            description='Retrieve and analyze a user\'s 3 most recent repositories on GitHub',
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "GitHub username (for example: 'kennethreitz' or 'tiangolo')",
                    }
                },
                "required": ["username"],
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """We're processing the tool call."""
    if name != "analyze_user_repos":
        raise ValueError(f"Unknown tool: {name}")

    if not arguments or "username" not in arguments:
        return [types.TextContent(type="text", text="Error: Missing argument 'username'.")]

    username = arguments["username"].strip()
    if not username:
        return [types.TextContent(type="text", text="Error: The username cannot be empty.")]

    async with httpx.AsyncClient() as client:
        try:
            api_url = f"https://api.github.com/users/{username}/repos"
            params = {"sort": "updated", "direction": "desc", "per_page": 3}
            headers = {"User-Agent": "MCP-Python-App"}

            response = await client.get(api_url, params=params, headers=headers)

            if response.status_code == 404:
                return [types.TextContent(type="text", text=f"Error: User with username '{username}' not found.")]
            elif response.status_code != 200:
                return [types.TextContent(type="text", text=f"GitHub API returned an error: {response.status_code}")]

            repos = response.json()

            if not repos:
                return [types.TextContent(type="text", text=f"User '{username}' does not have public repositories.")]

            report_lines = [f"=== Last 3 repositories user @{username} ==="]

            for idx, repo in enumerate(repos, 1):
                report_lines.append(
                    f"\n{idx}. Name: {repo.get('name')}\n"
                    f"   Link: {repo.get('html_url')}\n"
                    f"   Description: {repo.get('description') or 'No description'}\n"
                    f"   Primary language: {repo.get('language') or 'Not specified'}\n"
                    f"   Stars ⭐: {repo.get('stargazers_count')} | Forks 🍴: {repo.get('forks_count')}\n"
                    f"   Last updated: {repo.get('updated_at')}"
                )

            full_report = "\n".join(report_lines)
            return [types.TextContent(type="text", text=full_report)]

        except Exception as e:
            return [types.TextContent(type="text", text=f"An error occurred while making a request to GitHub: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="github-user-analyzer",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())