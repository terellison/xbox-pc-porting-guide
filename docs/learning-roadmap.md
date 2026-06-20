# Xbox Decompilation Learning Roadmap

A learning path for taking on an original Xbox reverse-engineering /
decompilation project — written for someone with solid C++ and some
Windows/DirectX exposure, but little reverse-engineering or game-runtime
background. Pairs with [`xbox-porting-guide.md`](../xbox-porting-guide.md)
and the [Ninja Gaiden Black case study](ninja-gaiden-black-case-study.md).

The good news: strong C++ already covers most of what you'll eventually
*write*. The gap is reading unfamiliar code (reverse-engineering skill) and
platform-specific knowledge (Xbox's particular quirks) — both learnable in
weeks, not years.

## 1. Reading disassembly (the actual new skill)

This is the biggest gap and the one that takes longest to build intuition
for.

- **x86 assembly, 32-bit only.** The Xbox CPU has no SSE2, so all floating
  point is x87 FPU code — it looks different from modern compiler output,
  and is a useful fingerprint for "is this float math" at a glance.
- **Calling conventions** — `cdecl` / `thiscall` / `stdcall`, how `this`
  gets passed, vtable layout for C++ virtual calls. Most of what you're
  reversing *is* C++, so recognizing vtable dispatch and
  constructor/destructor patterns is high-leverage early on.
- **[Ghidra](https://github.com/NationalSecurityAgency/ghidra)** (free, NSA)
  is the standard starting tool — its decompiler view turns disassembly
  into pseudo-C, a much gentler on-ramp than raw asm given a C++
  background. IDA Pro is the paid alternative with a more polished
  decompiler.
- **Compiler archaeology.** This was built with an early-2000s
  MSVC-derived toolchain. Learn to recognize *that specific compiler's*
  idioms — switch-jump tables, exception-handling tables, RTTI structures,
  presence/absence of `/GS` stack cookies — so you can tell "real game
  logic" apart from compiler boilerplate quickly. That distinction is most
  of what separates someone fast at this from someone slow.

## 2. Xbox-specific platform knowledge

- **The kernel ABI.** Xbox doesn't import kernel functions by name like
  Win32 — it imports by **ordinal number only**. Without an ordinal→name
  table, every kernel call just looks like `call [thunk_table+0x14]` with
  no label. [xboxdevwiki.net](https://xboxdevwiki.net/) publishes the
  table; Cxbx-Reloaded's and xemu's source also have it hardcoded.
- **The `.xbe` container format** — header, certificate, section table,
  the XOR-obfuscated entry point/kernel-thunk address. Already documented
  in this repo's [`toolkit/`](../toolkit/README.md), which parses it.
- **D3D8 on NV2A.** The original Xbox's Direct3D is D3D8-shaped but talks
  to a semi-custom GPU. [xemu](https://github.com/xemu-project/xemu) and
  [Cxbx-Reloaded](https://github.com/Cxbx-Reloaded/Cxbx-Reloaded) have
  already done the hard work of mapping NV2A register/pushbuffer behavior
  to modern D3D/Vulkan — their source is a better reference than any
  written doc.
- **Middleware fingerprinting.** Learn to recognize Unreal Engine 2,
  RenderWare, Bink video, Miles Sound System, etc. by string/section
  signatures. If a game uses one, you skip reversing large swaths of
  "someone else's already-documented engine" and focus only on the
  game-specific code layered on top.

## 3. Game runtime architecture

Concepts worth shoring up, given "dabbled but not deep": frame-loop
structure, scene graph/entity systems, animation blending,
collision/physics integration, asset streaming. You don't need to master
these in the abstract first — reverse-engineering one specific game's
version of each is actually an easier way to learn them than reading a
generic engine-architecture book.

## 4. Data format forensics

Distinct from code reversing: figuring out an unknown proprietary
compression/archive format from raw bytes — entropy analysis, looking for
known compression magic, then cross-referencing against the *loader code*
you've reversed to see how it parses the format. This is precisely where
the community [`DECOMP__Ninja`](https://github.com/mehmetalinya/DECOMP__Ninja)
project (attempting to decompile Ninja Gaiden Black/2) is currently stuck —
a good real example that this step is closer to cryptanalysis than to C++
skill, and can stall even strong reversers.

## 5. Workflow/tooling from existing decompilation communities

You don't have to invent the methodology. N64-era decompilation projects
(Super Mario 64, Zelda OoT/MM, Paper Mario) have spent years refining a
workflow: matching decompiled C against the original's compiled assembly
byte-for-byte (tools like `asm-differ`), function-by-function progress
tracking, and collaborative function-matching sites like decomp.me. The
same approach transfers directly to Xbox titles.

## 6. Legal practice: clean-room discipline

Worth internalizing early, not as an afterthought: keep a clear separation
between "people who read disassembly and write notes about behavior" and
"people who write the replacement implementation from those notes," and
never paste decompiler output directly into the reimplementation. This is
standard practice across decomp/clone projects for legal defensibility —
see the disclaimer in [`xbox-porting-guide.md`](../xbox-porting-guide.md).

## Learning resources

Structured material for the sections above, not just reference codebases:

| Resource | Covers |
|---|---|
| [Reverse Engineering for Beginners](https://beginners.re/) (Dennis Yurichev, free PDF) | The single best on-ramp for §1 — x86 asm, calling conventions, compiler-generated patterns, RTTI, all from a reversing angle rather than a generic assembly-language angle. |
| [OpenSecurityTraining2 — "Introductory x86"](https://opensecuritytraining.info/IntroX86.html) (free, video + slides + labs) | A real course (not just a doc) covering the same x86/calling-convention ground as §1, with hands-on labs. |
| [Agner Fog's calling conventions doc](https://www.agner.org/optimize/calling_conventions.pdf) ([agner.org/optimize](https://www.agner.org/optimize/)) | The canonical reference for `cdecl`/`thiscall`/`stdcall`, vtable layout, and register usage — useful to have open while reading Ghidra output. |
| [Ghidra docs and training](https://github.com/NationalSecurityAgency/ghidra) (built-in help + bundled cheat sheets) | The decompiler/tool itself, referenced in §1. |
| [decomp.me](https://decomp.me/) | Collaborative function-matching site from the N64 decomp community (§5) — practice matching decompiled C against compiled asm on real solved examples before trying it on an Xbox title. |
| [asm-differ](https://github.com/simonlindholm/asm-differ) | The diffing tool decomp projects use to check decompiled-and-recompiled output against the original byte-for-byte (§5). |
| [xboxdevwiki.net](https://xboxdevwiki.net/) | Not a course, but the closest thing to a living reference for §2 — kernel ordinal tables, `.xbe` format details, NV2A notes. |

None of these are Xbox-specific (no course teaches "Xbox decompilation" directly) — they teach the general x86/RE/decomp skills in §1 and §5, which you then apply to Xbox-specific knowledge from §2 by reading the reference projects below and the platform docs on xboxdevwiki.net. If you have access to someone who worked on original Xbox dev tooling or titles, that's a better resource than any doc for the undocumented quirks — ask them.

## Suggested starting point

Don't start with Ninja Gaiden Black, or anything else with known unsolved
blockers. Pick a small, well-understood game, extract it with
[`xboxport`](../toolkit/README.md), load `default.xbe` into Ghidra, and
get the `main`/frame-loop function identified and readable. That one win
teaches most of the workflow you'd reuse on anything harder.

## Reference projects worth reading the source of

| Project | Why it's useful |
|---|---|
| [Cxbx-Reloaded](https://github.com/Cxbx-Reloaded/Cxbx-Reloaded) | HLE kernel + D3D8→modern-API mapping, already reverse-engineered |
| [xemu](https://github.com/xemu-project/xemu) | Actively maintained, more accurate NV2A/GPU emulation |
| [nxdk](https://github.com/XboxDev/nxdk) | Modern Xbox SDK — shows what "correct" Xbox-side code looks like, for contrast against disassembly |
| [xbedump](https://github.com/XboxDev/xbedump) / [pyxbe](https://github.com/mborgerson/pyxbe) | Reference `.xbe` parsers to cross-check your own understanding |
| [DECOMP__Ninja](https://github.com/mehmetalinya/DECOMP__Ninja) | A real, currently-stalled attempt — read where it got stuck before duplicating effort |
