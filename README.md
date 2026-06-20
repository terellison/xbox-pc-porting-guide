# Xbox PC Porting Guide

A guide — and a small CLI to back it up — for taking an original Xbox
(1st gen) game you own and getting it running on Windows, whether that means
running it under a compatibility layer or fully decompiling and recompiling
it for native Windows.

This exists because games disappear: Team Ninja has confirmed the source
for *Ninja Gaiden Black* is lost, and it isn't the only one. See
[`docs/ninja-gaiden-black-case-study.md`](docs/ninja-gaiden-black-case-study.md)
for the concrete example that motivated this.

## Start here

1. Read [`xbox-porting-guide.md`](xbox-porting-guide.md) — the step-by-step
   guide (dump disc → inspect executable → pick a porting approach → build).
2. Use [`toolkit/`](toolkit/README.md) — the `xboxport` CLI that automates
   the disc-extraction and executable-inspection steps:

   ```bash
   cd toolkit && pip install -e .
   xboxport iso-extract game.iso ./extracted
   xboxport xbe-info ./extracted/default.xbe
   xboxport scaffold ./my-port --xbe ./extracted/default.xbe
   ```
3. Read [`docs/ninja-gaiden-black-case-study.md`](docs/ninja-gaiden-black-case-study.md)
   for a worked example, including a real, currently-stalled community
   decompilation effort worth checking before you start your own.

## Scope and legal stance

`xboxport` only ever reads two documented container formats — the XDVDFS
disc filesystem and the XBE executable header/certificate/section table —
the same category of work as reading ISO9660 or a PE header. It does not
disassemble code, does not interpret game logic, and ships no copyrighted
game data. The actual decompilation/reimplementation step is, and stays,
manual — see the disclaimer in `xbox-porting-guide.md`.

This is for games you own, for personal, educational, and preservation use.

## Repo layout

```
xbox-porting-guide.md                       step-by-step porting guide
docs/ninja-gaiden-black-case-study.md        worked example
toolkit/                                     xboxport CLI (Python)
  src/xboxport/xbe.py                        .xbe header/certificate/section parser
  src/xboxport/xiso.py                       XDVDFS (XISO) reader/extractor
  src/xboxport/scaffold.py                   project workspace + checklist generator
  src/xboxport/cli.py                        xboxport command-line entry point
  tests/                                     unit tests against synthetic fixtures
```
