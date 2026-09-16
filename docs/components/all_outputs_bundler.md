# all_outputs_bundler

## What it is
Packages the raw output of every other component into a single zip file, for debugging or manual inspection. Never runs automatically, only on an explicit request.

## How it works
Mirrors the engine's own folder structure inside the zip, so the layout is immediately familiar to anyone who's seen the codebase. Every input is optional, so it works correctly whether you want everything or just one piece.

Keeps the diff's raw and enriched versions as two separate files on purpose - if something looks wrong, this lets you tell whether the problem is in the comparison logic itself or in the later step that adds real source text.
