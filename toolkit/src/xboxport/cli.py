from __future__ import annotations

import argparse
import sys

from .scaffold import create_scaffold
from .xbe import XbeError, format_report, parse_xbe
from .xiso import XisoError, extract_iso, list_iso


def _cmd_xbe_info(args: argparse.Namespace) -> int:
    try:
        info = parse_xbe(args.xbe_path)
    except (XbeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(format_report(info))
    return 0


def _cmd_iso_list(args: argparse.Namespace) -> int:
    try:
        entries = list_iso(args.iso_path)
    except (XisoError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for e in entries:
        kind = "DIR " if e.is_directory else "FILE"
        print(f"{kind}  {e.size:>12}  {e.path}")
    return 0


def _cmd_iso_extract(args: argparse.Namespace) -> int:
    try:
        extracted = extract_iso(args.iso_path, args.out_dir)
    except (XisoError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Extracted {len(extracted)} file(s) to {args.out_dir}")
    return 0


def _cmd_scaffold(args: argparse.Namespace) -> int:
    info = None
    if args.xbe_path:
        try:
            info = parse_xbe(args.xbe_path)
        except (XbeError, OSError) as exc:
            print(f"warning: could not read XBE ({exc}); scaffolding without it", file=sys.stderr)
    path = create_scaffold(args.out_dir, info)
    print(f"Created project scaffold at {args.out_dir} ({path})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xboxport",
        description="Front-end tooling for porting an original Xbox game you own to PC.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_xbe = sub.add_parser("xbe-info", help="Inspect a default.xbe header/certificate/sections")
    p_xbe.add_argument("xbe_path")
    p_xbe.set_defaults(func=_cmd_xbe_info)

    p_list = sub.add_parser("iso-list", help="List the contents of an Xbox disc image (XISO)")
    p_list.add_argument("iso_path")
    p_list.set_defaults(func=_cmd_iso_list)

    p_extract = sub.add_parser("iso-extract", help="Extract every file from an XISO image")
    p_extract.add_argument("iso_path")
    p_extract.add_argument("out_dir")
    p_extract.set_defaults(func=_cmd_iso_extract)

    p_scaffold = sub.add_parser("scaffold", help="Create a porting project workspace + checklist")
    p_scaffold.add_argument("out_dir")
    p_scaffold.add_argument("--xbe", dest="xbe_path", help="Path to default.xbe to seed the checklist")
    p_scaffold.set_defaults(func=_cmd_scaffold)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
