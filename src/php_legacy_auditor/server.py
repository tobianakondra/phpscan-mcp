"""Server entrypoint: FastMCP server exposing the legacy PHP auditor tools.

Tools are read-only: none of them modifies, deletes, or executes the code
that is being audited.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("php-legacy-auditor")


@mcp.tool()
def get_auditor_status() -> dict:
    """Return the auditor status and the configured ALLOWED_AUDIT_ROOT."""
    return {"status": "ok", "allowed_audit_root": None}
