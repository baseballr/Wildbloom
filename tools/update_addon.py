#!/usr/bin/env python3
"""Puts a new Wildbloom build into the repo and updates the README's version lines.

usage: update_addon.py <Wildbloom-vX.Y.Z.mcaddon> [book-preview.txt]

Copies the build to content/Wildbloom.mcaddon (and the Lexicon text to content/lexicon.txt if given),
then rewrites the README lines between the wildbloom-version markers from the pack's manifest:
add-on version and the supported Minecraft range (min_engine_version to the latest release).
"""
import json, os, re, shutil, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
addon = sys.argv[1]

with zipfile.ZipFile(addon) as zf:
    path = next(n for n in zf.namelist() if n.endswith("Wildbloom_BP/manifest.json"))
    header = json.loads(zf.read(path))["header"]
version = ".".join(map(str, header["version"]))
min_engine = ".".join(map(str, header["min_engine_version"]))

shutil.copyfile(addon, os.path.join(ROOT, "content", "Wildbloom.mcaddon"))
if len(sys.argv) > 2:
    shutil.copyfile(sys.argv[2], os.path.join(ROOT, "content", "lexicon.txt"))

readme_path = os.path.join(ROOT, "README.md")
readme = open(readme_path, encoding="utf-8").read()
block = (
    "<!-- wildbloom-version -->\n"
    f"**Add-on version:** v{version} ([download](content/Wildbloom.mcaddon))  \n"
    f"**Works with:** Minecraft Bedrock {min_engine} – latest\n"
    "<!-- /wildbloom-version -->"
)
readme = re.sub(r"<!-- wildbloom-version -->.*?<!-- /wildbloom-version -->", block, readme, flags=re.S)
open(readme_path, "w", encoding="utf-8").write(readme)
print(f"Wildbloom v{version}, Minecraft Bedrock {min_engine} – latest")
