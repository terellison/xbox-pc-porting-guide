# Case study: Ninja Gaiden Black

*Ninja Gaiden Black* (2005, Team Ninja, original Xbox exclusive) is a good
test case for this guide because it has the exact problem this repo exists
to address: **the original source is gone.**

## What's actually known

- Team Ninja has confirmed it lost the source code for *Ninja Gaiden Black*
  and *Ninja Gaiden 2*. When Koei Tecmo put together the *Ninja Gaiden:
  Master Collection*, it had to build from the *Sigma* re-releases instead,
  because Black/NG2's own source wasn't recoverable.
  ([CBR](https://www.cbr.com/ninja-gaiden-black-master-collection-source-code/))
- There's an existing community effort,
  [`mehmetalinya/DECOMP__Ninja`](https://github.com/mehmetalinya/DECOMP__Ninja),
  attempting exactly the "decompile from the disc" path this guide
  describes. As of last check it's stalled on reverse-engineering the
  game's custom compression/encryption formats — the disc's data files use
  unidentified algorithms, and forensics on those formats is blocking
  further progress. **Check this project before duplicating its work.**
- Separately, [xemu](https://xemu.app/titles/5443000d/) already runs
  *Ninja Gaiden Black* as "playable with minor issues" via HLE emulation —
  no decompilation involved. Cxbx-Reloaded's last public compatibility
  report (its `game-compatibility` tracker was archived in 2021) had it
  booting to the menu but failing to render gameplay; xemu has since
  surpassed that.

## What this means for "porting" it

If the goal is *playing* Ninja Gaiden Black on PC today, xemu already gets
you there with no legal/technical risk beyond owning the disc — that's
Approach A in the main guide, and it's almost certainly the right starting
point.

If the goal is *preservation* — a real decompiled, buildable, native
Windows version, independent of emulation — that's the harder Approach C
path, and it's exactly what `DECOMP__Ninja` is attempting. The blocker
isn't disassembly or porting Win32 calls; it's that nobody has yet cracked
the proprietary archive/compression format the disc's asset files use. That
forensics step has to happen before `xboxport iso-extract`'s output (the
raw archive files) becomes useful for anything beyond inspection.

## Where `xboxport` fits

`xboxport` gets you the first two steps for free and gives you something
concrete to compare against `DECOMP__Ninja`'s findings:

```bash
xboxport iso-list ngb.iso          # confirm the archive/file layout matches what others have documented
xboxport iso-extract ngb.iso ./extracted
xboxport xbe-info ./extracted/default.xbe   # entry point, sections, certificate (title ID, region, disk #)
```

Past that point you're in genuine reverse-engineering territory (the
unidentified compression format), which is exactly the kind of
game-specific, copyrighted-code-adjacent work this toolkit deliberately
does *not* automate.
