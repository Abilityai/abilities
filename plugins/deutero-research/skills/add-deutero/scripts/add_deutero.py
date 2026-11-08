#!/usr/bin/env python3
"""Give a running Trinity agent Deutero: one API key and one MCP server.

Trinity's inject endpoint replaces whole files, so this script reads the
agent's current `.env` and `.mcp.json`, merges Deutero in, and writes both
back. Everything else in those files is kept as it was.

  * `.env`      gains (or updates) DEUTERO_API_KEY=<key>
  * `.mcp.json` gains (or updates) a `deutero` server:
        {"type": "http", "url": "https://dashboard.deutero.ai/mcp",
         "headers": {"X-API-Key": "${DEUTERO_API_KEY}"}}
    The header is a placeholder; Claude Code fills it in from the agent's
    environment, so the key itself never sits in .mcp.json.

The Deutero key is read from a file or the DEUTERO_API_KEY environment
variable and is never printed. Trinity's URL and API key come from the
`/trinity:connect` profile (~/.trinity/config.json) unless TRINITY_URL and
TRINITY_API_KEY are set.

Standard library only. Prints one JSON summary line; exit 0 on success.

Usage:
  add_deutero.py --agent NAME [--key-file PATH] [--dry-run] [--no-verify] [--force]
  add_deutero.py --agent NAME --remove
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEUTERO_MCP_URL = "https://dashboard.deutero.ai/mcp"
DEUTERO_REST_CHECK = "https://dashboard.deutero.ai/study-api/api/v1/projects"
ENV_VAR = "DEUTERO_API_KEY"
SERVER_NAME = "deutero"
SERVER_ENTRY = {
    "type": "http",
    "url": DEUTERO_MCP_URL,
    "headers": {"X-API-Key": "${" + ENV_VAR + "}"},
}
DEFAULT_KEY_FILE = Path.home() / ".config" / "deutero" / "api_key"
HOME = "/home/developer"
_ENV_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")


class Fail(Exception):
    """A clean, user-facing failure. Never carries a secret."""


def _out(**fields) -> None:
    print(json.dumps(fields, sort_keys=True))


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------


def trinity_target() -> tuple[str, str]:
    url = os.environ.get("TRINITY_URL")
    key = os.environ.get("TRINITY_API_KEY")
    if url and key:
        return url.rstrip("/"), key
    cfg_path = Path.home() / ".trinity" / "config.json"
    if not cfg_path.exists():
        raise Fail("No Trinity profile found. Run /trinity:connect first, "
                   "or set TRINITY_URL and TRINITY_API_KEY.")
    cfg = json.loads(cfg_path.read_text())
    profile = cfg.get("profiles", {}).get(cfg.get("current_profile", ""), {})
    url = profile.get("instance_url")
    key = profile.get("mcp_api_key") or profile.get("token")
    if not url or not key:
        raise Fail("The current Trinity profile has no instance_url or API key. "
                   "Run /trinity:connect --force.")
    return url.rstrip("/"), key


def deutero_key(key_file: str | None) -> str:
    if key_file:
        path = Path(key_file).expanduser()
        if not path.exists():
            raise Fail(f"Key file not found: {path}")
        key = path.read_text().strip()
    elif os.environ.get(ENV_VAR):
        key = os.environ[ENV_VAR].strip()
    elif DEFAULT_KEY_FILE.exists():
        key = DEFAULT_KEY_FILE.read_text().strip()
    else:
        raise Fail(f"No Deutero key. Put it in {DEFAULT_KEY_FILE} (chmod 600), "
                   f"pass --key-file, or set {ENV_VAR}.")
    if not key or any(c.isspace() for c in key) or "\n" in key:
        raise Fail("The Deutero key is empty or contains whitespace.")
    return key


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------


def _request(method: str, url: str, headers: dict, body: bytes | None = None,
             timeout: float = 30.0) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except urllib.error.URLError as e:
        raise Fail(f"Could not reach {urllib.parse.urlsplit(url).netloc}: {e.reason}")


def verify_deutero_key(key: str) -> None:
    status, _ = _request("GET", DEUTERO_REST_CHECK,
                         {"X-API-Key": key, "Accept": "application/json"})
    if status in (401, 403):
        raise Fail(f"Deutero rejected the key (HTTP {status}). Generate a new one "
                   "in Deutero: Settings -> Generate API Key.")
    if status != 200:
        raise Fail(f"Deutero key check returned HTTP {status}; try again shortly, "
                   "or rerun with --no-verify.")


class Trinity:
    def __init__(self, base: str, key: str, agent: str):
        self.base, self.agent = base, agent
        self.headers = {"Authorization": f"Bearer {key}"}

    def _agent_url(self, suffix: str) -> str:
        return f"{self.base}/api/agents/{urllib.parse.quote(self.agent)}{suffix}"

    def check_running(self) -> None:
        status, body = _request("GET", self._agent_url(""), self.headers)
        if status == 404:
            raise Fail(f"Agent '{self.agent}' not found, or you do not own it.")
        if status in (401, 403):
            raise Fail(f"Trinity refused the request (HTTP {status}). Only the agent's "
                       "owner (or an admin), signed in as a person, can change its "
                       "credentials. Run /trinity:connect.")
        if status != 200:
            raise Fail(f"Trinity returned HTTP {status} for agent '{self.agent}'.")
        info = json.loads(body or b"{}")
        if info.get("status") not in (None, "running"):
            raise Fail(f"Agent '{self.agent}' is {info.get('status')}. Start it first.")

    def read_file(self, name: str) -> str:
        """Current contents of ~/<name>, or '' when it does not exist."""
        url = self._agent_url("/files/download?path=" +
                              urllib.parse.quote(f"{HOME}/{name}", safe=""))
        status, body = _request("GET", url, self.headers)
        if status == 404:
            return ""
        if status != 200:
            raise Fail(f"Could not read the agent's {name} (HTTP {status}). "
                       "Reading credential files needs owner access.")
        return body.decode("utf-8")

    def inject(self, files: dict[str, str]) -> None:
        body = json.dumps({"files": files}).encode()
        status, resp = _request(
            "POST", self._agent_url("/credentials/inject"),
            {**self.headers, "Content-Type": "application/json"}, body)
        if status != 200:
            detail = ""
            try:
                detail = json.loads(resp).get("detail", "")
            except (ValueError, AttributeError):
                pass
            if not isinstance(detail, str):
                detail = json.dumps(detail)[:300]
            raise Fail(f"Trinity refused the write (HTTP {status}). {detail}".strip())


# --------------------------------------------------------------------------
# Merging
# --------------------------------------------------------------------------


def merge_env(text: str, key: str | None) -> tuple[str, str]:
    """Set (key given) or remove (key None) DEUTERO_API_KEY. Other lines are
    kept byte for byte. Returns (new_text, action)."""
    lines = text.splitlines()
    found, out = False, []
    for line in lines:
        m = _ENV_LINE.match(line)
        if m and m.group(1) == ENV_VAR:
            if key is None or found:
                found = True
                continue  # drop (removal, or a duplicate)
            found = True
            if line.split("=", 1)[1].strip().strip("'\"") == key:
                out.append(line)
                continue
            out.append(f"{ENV_VAR}={key}")
            continue
        out.append(line)
    if key is None:
        action = "removed" if found else "absent"
    elif not found:
        out.append(f"{ENV_VAR}={key}")
        action = "added"
    else:
        action = "unchanged" if out == lines else "updated"
    new = "\n".join(out)
    if new and not new.endswith("\n"):
        new += "\n"
    return new, action


def merge_mcp(text: str, remove: bool, force: bool) -> tuple[str, str]:
    if text.strip():
        try:
            cfg = json.loads(text)
        except ValueError:
            raise Fail("The agent's .mcp.json is not valid JSON; fix it before adding Deutero.")
    else:
        cfg = {}
    if not isinstance(cfg, dict):
        raise Fail("The agent's .mcp.json is not a JSON object.")
    servers = cfg.setdefault("mcpServers", {})
    current = servers.get(SERVER_NAME)
    if remove:
        if current is None:
            return text, "absent"
        del servers[SERVER_NAME]
        action = "removed"
    elif current == SERVER_ENTRY:
        return text, "unchanged"
    elif current is not None and not force:
        raise Fail("The agent already has a different 'deutero' MCP server. "
                   "Rerun with --force to replace it.")
    else:
        action = "updated" if current is not None else "added"
        servers[SERVER_NAME] = SERVER_ENTRY
    return json.dumps(cfg, indent=2) + "\n", action


# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--agent", required=True)
    ap.add_argument("--key-file")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would change; write nothing.")
    ap.add_argument("--no-verify", action="store_true",
                    help="Skip the Deutero key check.")
    ap.add_argument("--force", action="store_true",
                    help="Replace an existing, different 'deutero' MCP entry.")
    ap.add_argument("--remove", action="store_true",
                    help="Remove the Deutero key and MCP server instead.")
    args = ap.parse_args()

    try:
        base, tkey = trinity_target()
        key = None if args.remove else deutero_key(args.key_file)
        if key and not args.no_verify:
            verify_deutero_key(key)

        trinity = Trinity(base, tkey, args.agent)
        trinity.check_running()
        env_new, env_action = merge_env(trinity.read_file(".env"), key)
        mcp_new, mcp_action = merge_mcp(trinity.read_file(".mcp.json"),
                                        args.remove, args.force)

        files = {}
        if env_action in ("added", "updated", "removed"):
            files[".env"] = env_new
        if mcp_action in ("added", "updated", "removed"):
            files[".mcp.json"] = mcp_new
        if files and not args.dry_run:
            trinity.inject(files)

        _out(ok=True, agent=args.agent, instance=base, dry_run=args.dry_run,
             env=env_action, mcp=mcp_action,
             key_check="skipped" if (args.no_verify or args.remove) else "valid",
             written=sorted(files) if not args.dry_run else [])
        return 0
    except Fail as e:
        _out(ok=False, agent=args.agent, error=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
