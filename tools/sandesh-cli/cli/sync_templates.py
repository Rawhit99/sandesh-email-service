"""Sync email templates from one Sandesh API to another via HTTP."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import httpx


def _norm_base(url: str) -> str:
    return url.rstrip("/")


def _auth_headers(api_key: str, org_id: str | None) -> dict[str, str]:
    h: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if org_id and org_id.strip():
        h["X-Sandesh-Organization-Id"] = org_id.strip()
    return h


def _detail_message(resp: httpx.Response) -> str:
    try:
        data = resp.json()
    except Exception:
        return resp.text or resp.reason_phrase
    detail = data.get("detail")
    if isinstance(detail, list):
        return " ".join(
            str(x) if not isinstance(x, dict) else json.dumps(x) for x in detail
        )
    return str(detail) if detail is not None else resp.text or resp.reason_phrase


def _fetch_all_templates(
    client: httpx.Client,
    base: str,
    headers: dict[str, str],
    active_only: bool,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    offset = 0
    limit = 100
    while True:
        r = client.get(
            f"{base}/api/v1/templates",
            params={"limit": limit, "offset": offset, "active_only": active_only},
            headers=headers,
        )
        if r.status_code >= 400:
            raise RuntimeError(
                f"List templates failed ({r.status_code}): {_detail_message(r)}"
            )
        batch = r.json()
        if not batch:
            break
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected list templates response (not a list)")
        out.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
    return out


def _upsert_template(
    client: httpx.Client,
    base: str,
    headers: dict[str, str],
    tpl: dict[str, Any],
    dry_run: bool,
) -> str:
    """Replicate one template: always PUT (full overwrite); POST only if missing (404)."""
    tid = str(tpl["template_id"])
    update_body: dict[str, Any] = {
        "name": tpl["name"],
        "subject": tpl["subject"],
        "content": tpl["content"],
        "variables": tpl.get("variables") or {},
        "is_active": bool(tpl.get("is_active", True)),
    }
    create_body: dict[str, Any] = {"template_id": tid, **update_body}
    if dry_run:
        return f"dry-run: would replicate {tid}"

    r = client.put(
        f"{base}/api/v1/templates/{tid}",
        json=update_body,
        headers=headers,
    )
    if r.status_code in (200, 201):
        return f"replicated {tid} (updated)"

    if r.status_code == 404:
        r2 = client.post(
            f"{base}/api/v1/templates",
            json=create_body,
            headers=headers,
        )
        if r2.status_code in (200, 201):
            return f"replicated {tid} (created)"
        raise RuntimeError(
            f"Create {tid} after missing on dest failed ({r2.status_code}): "
            f"{_detail_message(r2)}"
        )

    raise RuntimeError(
        f"Update {tid} failed ({r.status_code}): {_detail_message(r)}"
    )


def run_sync(args: argparse.Namespace) -> int:
    source_base = _norm_base(args.source_url)
    dest_base = _norm_base(args.dest_url)
    src_headers = _auth_headers(args.source_key, args.source_org_id)
    dst_headers = _auth_headers(args.dest_key, args.dest_org_id)

    timeout = httpx.Timeout(args.timeout)
    with httpx.Client(timeout=timeout) as client:
        templates = _fetch_all_templates(
            client,
            source_base,
            src_headers,
            active_only=args.active_only,
        )
        print(f"Source: {len(templates)} template(s) to sync.", file=sys.stderr)
        ok = 0
        for tpl in templates:
            try:
                line = _upsert_template(
                    client, dest_base, dst_headers, tpl, args.dry_run
                )
                print(line)
                ok += 1
            except Exception as e:
                print(f"ERROR {tpl.get('template_id')}: {e}", file=sys.stderr)
                if not args.continue_on_error:
                    return 1
        print(f"Done. {ok}/{len(templates)} processed.", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sandesh",
        description="Sandesh CLI (template sync between environments).",
    )
    parser.add_argument(
        "--version",
        "-version",
        action="version",
        version="sandesh-cli 0.1.0",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_sync(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--source-url",
            required=True,
            metavar="URL",
            help="Source Sandesh API base URL (e.g. https://dev.example.com:8000)",
        )
        p.add_argument(
            "--source-key",
            required=True,
            metavar="KEY",
            help="Source API key (Bearer token sent as Authorization)",
        )
        p.add_argument(
            "--dest-url",
            required=True,
            metavar="URL",
            help="Destination Sandesh API base URL",
        )
        p.add_argument(
            "--dest-key",
            required=True,
            metavar="KEY",
            help="Destination API key",
        )
        p.add_argument(
            "--source-org-id",
            default=None,
            help="Optional X-Sandesh-Organization-Id for source (platform admin)",
        )
        p.add_argument(
            "--dest-org-id",
            default=None,
            help="Optional X-Sandesh-Organization-Id for destination (platform admin)",
        )
        p.add_argument(
            "--active-only",
            action="store_true",
            help="Only sync templates that are active on the source",
        )
        p.add_argument(
            "--dry-run",
            action="store_true",
            help="List actions without calling destination create/update",
        )
        p.add_argument(
            "--continue-on-error",
            action="store_true",
            help="Keep syncing after a template fails",
        )
        p.add_argument(
            "--timeout",
            type=float,
            default=120.0,
            help="HTTP timeout seconds (default: 120)",
        )

    add_sync(sub.add_parser("sync-templates", help="Copy all templates to another Sandesh server"))
    add_sync(sub.add_parser("sync-template", help="Alias of sync-templates"))

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command in ("sync-templates", "sync-template"):
        raise SystemExit(run_sync(args))
    raise SystemExit(2)
