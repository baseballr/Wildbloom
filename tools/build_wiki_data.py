#!/usr/bin/env python3
"""Builds the wiki's data and images from a Wildbloom .mcaddon and the Lexicon text.

usage: build_wiki_data.py <Wildbloom.mcaddon> <lexicon.txt> <bosses.png> <wwwroot>

Writes <wwwroot>/data/wiki.json and <wwwroot>/img/{items,blocks,bosses}/*.png.
Re-run it whenever the add-on changes; nothing in the site is hand-entered.
"""
import io, json, math, os, re, sys, zipfile
from PIL import Image, ImageDraw

ADDON, LEXICON, BOSS_SHEET, OUT = sys.argv[1:5]

zf = zipfile.ZipFile(ADDON)
names = zf.namelist()


def find(suffix):
    hits = [n for n in names if n.endswith(suffix)]
    return hits[0] if hits else None


def read_json(path):
    text = zf.read(path).decode("utf-8")
    text = re.sub(r"^\s*//.*$", "", text, flags=re.M)
    return json.loads(text)


def bp(rel):
    return [n for n in names if re.search(r"(^|/)Wildbloom_BP/" + rel, n)]


def rp(rel):
    return [n for n in names if re.search(r"(^|/)Wildbloom_RP/" + rel, n)]


def image(path):
    return Image.open(io.BytesIO(zf.read(path))).convert("RGBA")


# ---------------------------------------------------------------- names
lang = {}
for line in zf.read(find("Wildbloom_BP/texts/en_US.lang")).decode("utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        lang[k.strip()] = v.strip()

manifest = read_json(find("Wildbloom_BP/manifest.json"))
version = ".".join(str(x) for x in manifest["header"]["version"])

VANILLA = {
    "ender_eye": "Eye of Ender", "tnt": "TNT", "heart_of_the_sea": "Heart of the Sea",
    "*_log": "any Log", "glass_pane": "Glass Pane", "rabbit_foot": "Rabbit's Foot",
    "lapis_lazuli": "Lapis Lazuli", "nether_wart": "Nether Wart", "planks": "any Planks",
}


def vanilla_name(vid):
    short = vid.split(":", 1)[-1]
    if short in VANILLA:
        return VANILLA[short]
    if short.startswith("*_"):
        return "any " + short[2:].replace("_", " ").title()
    return short.replace("_", " ").title()


# ---------------------------------------------------------------- data.js
datajs = zf.read(find("scripts/data.js")).decode("utf-8")


def js_const(name):
    m = re.search(r"export const " + name + r" = (.*?);\s*(?=export|\Z)", datajs, re.S)
    return json.loads(m.group(1))


FLOWERS = js_const("FLOWERS")
FUNCTIONAL = js_const("FUNCTIONAL")
POOLS = js_const("POOLS")
ACCEPTORS = js_const("ACCEPTORS")
POOL_RECIPES = js_const("POOL_RECIPES")
ALTAR_RECIPES = js_const("ALTAR_RECIPES")
BREWERY_RECIPES = js_const("BREWERY_RECIPES")
ENCHANT_RUNES = js_const("ENCHANT_RUNES")
BOSSES = js_const("BOSSES")
TOOL_MAX_CHARGE = js_const("TOOL_MAX_CHARGE")
BATTERY_CAP = js_const("BATTERY_CAP")

# ---------------------------------------------------------------- items & blocks
items = {}
for path in bp(r"items/.*\.json$"):
    d = read_json(path)["minecraft:item"]
    iid = d["description"]["identifier"]
    items[iid] = {"id": iid, "kind": "item", "name": lang.get(f"item.{iid}.name", iid)}
for path in bp(r"blocks/.*\.json$"):
    d = read_json(path)["minecraft:block"]
    iid = d["description"]["identifier"]
    items[iid] = {"id": iid, "kind": "block", "name": lang.get(f"tile.{iid}.name", iid),
                  "_components": d.get("components", {})}


def display(iid):
    return items[iid]["name"] if iid in items else vanilla_name(iid)


def category(iid):
    s = iid.split(":")[1]
    if iid in FLOWERS:
        return "Generating Flowers"
    if s.startswith("fn_"):
        return "Helper Flowers"
    if s.startswith("mana_pool"):
        return "Mana Pools"
    if s in ("mana_spreader", "mana_relay", "mana_prism", "mana_gate", "sun_mirror", "spark") or s.startswith("lens_"):
        return "Mana Network"
    if s in ("mana_furnace", "mana_cannon", "mana_elevator", "mana_brewery", "mana_enchanter", "mana_gauge",
             "rune_altar", "ritual_altar", "sacrificial_altar", "wind_vane", "crystal_heart"):
        return "Machines & Altars"
    if s.startswith("rune_"):
        return "Runes"
    if s in ("thorn_seed", "crystal_idol", "warden_sigil"):
        return "Ritual Keys"
    if re.search(r"_(helmet|chestplate|leggings|boots)$", s):
        return "Armor"
    if re.search(r"_(sword|pickaxe|axe|shovel|bow)$", s) or s in ("terra_blade", "gale_glaive", "terraformer"):
        return "Tools & Weapons"
    if s.startswith("flask_") or s == "glass_vial":
        return "Flasks"
    if items[iid]["kind"] == "block":
        return "Building Blocks"
    if s in ("mana_ingot", "mana_diamond", "mana_crystal", "verdant_alloy", "fae_steel", "heartwood"):
        return "Materials"
    return "Trinkets & Items"


CATEGORY_ORDER = ["Materials", "Generating Flowers", "Helper Flowers", "Mana Pools", "Mana Network",
                  "Machines & Altars", "Runes", "Ritual Keys", "Tools & Weapons", "Armor", "Trinkets & Items",
                  "Flasks", "Building Blocks"]

# ---------------------------------------------------------------- recipes
recipes = []
for path in sorted(bp(r"recipes/.*\.json$")):
    d = read_json(path)
    key = next(k for k in d if k.startswith("minecraft:recipe"))
    r = d[key]
    res = r["result"]
    res = res if isinstance(res, dict) else {"item": res}
    rec = {"type": "crafting", "output": res["item"], "count": res.get("count", 1)}
    if key == "minecraft:recipe_shaped":
        rec["pattern"] = r["pattern"]
        rec["key"] = {k: (v["item"] if isinstance(v, dict) else v) for k, v in r["key"].items()}
        rec["ingredients"] = sorted(set(rec["key"].values()))
    else:
        rec["ingredients"] = [(i["item"] if isinstance(i, dict) else i) for i in r["ingredients"]]
    recipes.append(rec)


def min_pool(cost):
    for pid in ("wb:mana_pool_small", "wb:mana_pool", "wb:mana_pool_grand"):
        if POOLS[pid]["cap"] >= cost:
            return pid
    return "wb:mana_pool_grand"


for r in POOL_RECIPES:
    recipes.append({"type": "pool", "output": r["out"], "count": 1, "ingredients": r["ingredients"],
                    "cost": r["cost"], "station": min_pool(r["cost"])})
for r in ALTAR_RECIPES:
    recipes.append({"type": "altar", "output": r["out"], "count": 1, "ingredients": r["ingredients"],
                    "cost": r["cost"], "station": "wb:rune_altar"})
for r in BREWERY_RECIPES:
    recipes.append({"type": "brewery", "output": r["out"], "count": 1, "ingredients": r["ingredients"],
                    "cost": r["cost"], "station": "wb:mana_brewery"})

# ---------------------------------------------------------------- lexicon text
lex_lines = open(LEXICON, encoding="utf-8").read().splitlines()


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


chapters = []
cur = sec = None
for line in lex_lines:
    if line.startswith("##### "):
        title = re.sub(r"\s*\[.*\]\s*$", "", line[6:]).strip()
        cur = {"title": title, "slug": slugify(title), "intro": [], "sections": []}
        chapters.append(cur)
        sec = None
    elif line.startswith("=== "):
        title = line[4:].strip()
        sec = {"title": title, "slug": slugify(title), "lines": []}
        cur["sections"].append(sec)
    elif cur is not None:
        (sec["lines"] if sec else cur["intro"]).append(line)


def trim(lines):
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return lines


for ch in chapters:
    ch["intro"] = trim(ch["intro"])
    for s in ch["sections"]:
        s["lines"] = trim(s["lines"])

by_name = {v["name"].lower(): k for k, v in items.items()}
by_name["livingwood planks"] = "wb:livingwood"
by_name["mana spark"] = "wb:spark"
by_name["terraformer wand"] = "wb:terraformer"


def cut_recipe(lines):
    """Drop the 'How to make' part; the site draws recipes from the real recipe data."""
    out = []
    for ln in lines:
        if ln.strip() == "How to make":
            break
        out.append(ln)
    return trim(out)


# Each item gets the lexicon text written about it: a whole === section, or an inline entry
# ("Mana Axe  7 dmg, ..." followed by indented lines).
for ch in chapters:
    for s in ch["sections"]:
        name = re.sub(r"\s+T\d$", "", s["title"]).lower()
        iid = by_name.get(name)
        if iid and "text" not in items[iid]:
            body = s["lines"]
            if body and body[0].split("  ")[0].strip().lower() == name:
                head = body[0].split("  ", 1)
                if len(head) > 1:
                    items[iid]["stats"] = head[1].strip()
                body = body[1:]
            items[iid]["text"] = cut_recipe(body)
            items[iid]["guide"] = f"{ch['slug']}#{s['slug']}"

for ch in chapters:
    for s in [{"slug": "", "lines": ch["intro"]}] + ch["sections"]:
        lines = s["lines"]
        for i, ln in enumerate(lines):
            if ln.startswith(" ") or "  " not in ln:
                continue
            name, meta = ln.split("  ", 1)
            iid = by_name.get(name.strip().lower())
            if not iid or "text" in items[iid]:
                continue
            desc = []
            for nxt in lines[i + 1:]:
                if not nxt.startswith("  ") or nxt.startswith("   ["):
                    break
                t = nxt.strip()
                if re.match(r"^(Crafting table|shaped|shapeless)", t):
                    break
                desc.append(t)
            items[iid]["stats"] = meta.strip()
            items[iid]["text"] = [d for d in desc if not (" + " in d and not d.endswith("."))]
            items[iid]["guide"] = ch["slug"] + (f"#{s['slug']}" if s["slug"] else "")

# a heading line that is exactly an item name, followed by a paragraph ("Velocity Lens\nRange 48...")
for ch in chapters:
    for s in [{"slug": "", "lines": ch["intro"]}] + ch["sections"]:
        lines = s["lines"]
        for i, ln in enumerate(lines):
            iid = by_name.get(ln.strip().lower())
            if ln.startswith(" ") or not iid or items[iid].get("text"):
                continue
            desc = []
            for nxt in lines[i + 1:]:
                t = nxt.strip()
                if not t or re.match(r"^(Crafting table|shaped|shapeless|How to make)", t) or by_name.get(t.lower()):
                    break
                desc.append(t)
            if desc:
                items[iid]["text"] = desc
                items[iid]["guide"] = ch["slug"] + (f"#{s['slug']}" if s["slug"] else "")

# a chapter named after an item describes it in its intro ("Rune Altar", "Rituals")
CHAPTER_ITEM = {"rune-altar": "wb:rune_altar", "rituals": "wb:ritual_altar"}
for ch in chapters:
    iid = CHAPTER_ITEM.get(ch["slug"])
    if iid and not items[iid].get("text"):
        items[iid]["text"] = cut_recipe(ch["intro"]) or cut_recipe(ch["sections"][0]["lines"] if ch["sections"] else [])
        items[iid]["guide"] = ch["slug"]

# tool tiers with no ability text: use the section's one-line description
for ch in chapters:
    for s in ch["sections"]:
        first = next((l for l in s["lines"] if l.strip()), "")
        for ln in s["lines"]:
            if ln.startswith(" ") or "  " not in ln:
                continue
            iid = by_name.get(ln.split("  ")[0].strip().lower())
            if iid and not items[iid].get("text"):
                items[iid]["text"] = [first]

# pools: "  Small Mana Pool: holds 5,000"
for ln in lex_lines:
    m = re.match(r"^\s+([^:]+):\s*(holds .*)$", ln)
    if m and by_name.get(m.group(1).strip().lower()):
        iid = by_name[m.group(1).strip().lower()]
        items[iid].setdefault("stats", m.group(2)[0].upper() + m.group(2)[1:])

FALLBACK = {
    "wb:heartwood": ["Dropped by the Heartwood Warden (4-8 per kill). Crafts the Heartwood tools and armor, the strongest in Wildbloom."],
    "wb:mana_crystal": ["Mined from Mana Crystal Ore (1-3 each) and dropped by the Crystal Sentinel. Crafts the Crystal Idol and the Crystal Heart."],
    "wb:lexicon": ["The in-game guide to Wildbloom. Everything on this wiki is also in the Lexicon."],
    "wb:mana_pool_overflow": ["Once over 90% full, it pushes 500 mana a second into every pool touching it. Put it in the middle of your flowers and chain normal pools to it."],
    "wb:glass_vial": ["A small glass container."],
    "wb:living_sapling": ["Plant it on dirt or grass with 6 empty blocks above. It grows into a Livingwood tree whose trunk logs make mana."],
    "wb:mana_pool_small": ["The first pool. Flowers within 6 blocks fill it, and items dropped on it are infused once it holds enough mana."],
    "wb:mana_pool": ["The standard pool. Needed for recipes that cost more than 5,000 mana, such as the Mana Diamond."],
    "wb:mana_pool_grand": ["The largest pool. Needed for tier 4 flowers and the big rituals."],
}
for iid, text in FALLBACK.items():
    if iid in items and not items[iid].get("text"):
        items[iid]["text"] = text

# armor sets: "Mana armor  15 armor points total" + "  Full set bonus: ..."
for ch in chapters:
    if ch["slug"] != "armor":
        continue
    lines = ch["intro"]
    for i, ln in enumerate(lines):
        m = re.match(r"^(\w+) armor\s{2,}(.*)$", ln)
        if not m:
            continue
        bonus = lines[i + 1].strip() if i + 1 < len(lines) else ""
        for piece in ("helmet", "chestplate", "leggings", "boots"):
            iid = f"wb:{m.group(1).lower()}_{piece}"
            if iid in items:
                items[iid]["stats"] = f"{m.group(1)} set: {m.group(2)}"
                items[iid]["text"] = [bonus]
                items[iid]["guide"] = "armor"

# ---------------------------------------------------------------- flowers
flower_tier = {}
flower_text = {}
for ch in chapters:
    for s in ch["sections"]:
        m = re.match(r"^(.*) T(\d)$", s["title"])
        if m:
            flower_tier[m.group(1).lower()] = int(m.group(2))

TRIGGER = {
    "sun": "Daylight, open sky", "adjacent": "Touching blocks", "items": "Eats dropped items",
    "night": "Night (or below Y=30)", "crops": "Grown crops nearby", "mobkill": "Mob deaths nearby",
    "altitude": "High altitude", "moon": "Night, full moon", "burn": "Burns blocks",
    "lightning": "Lightning strikes", "dimension": "Other dimensions",
}
flowers = []
for iid, f in FLOWERS.items():
    flowers.append({
        "id": iid, "tier": flower_tier.get(f["name"].lower(), 1), "trigger": TRIGGER.get(f["trigger"], f["trigger"]),
        "output": f.get("output", 0),
        "accepts": [{"id": k, "name": display(k), "mana": v} for k, v in sorted(f.get("items", {}).items(), key=lambda kv: -kv[1])],
    })
helpers = []
for key, f in FUNCTIONAL.items():
    helpers.append({"id": f"wb:fn_{key}", "radius": f["radius"], "cost": f["cost"]})

# ---------------------------------------------------------------- bosses
boss_text = {}
for ch in chapters:
    if ch["slug"] != "bosses":
        continue
    for s in ch["sections"]:
        lines = s["lines"][1:]
        stats = lines[0] if lines else ""
        parts, cur_h = {}, None
        for ln in lines[1:]:
            if ln.strip() in ("Summoning", "The fight", "Strategy", "Drops"):
                cur_h = ln.strip()
                parts[cur_h] = []
            elif cur_h and ln.strip():
                parts[cur_h].append(ln.strip().lstrip("- ").strip())
        boss_text[s["title"]] = {"stats": stats, **parts}

boss_keys = {"wb:crystal_sentinel": "wb:crystal_idol", "wb:thornmother": "wb:thorn_seed",
             "wb:heartwood_warden": "wb:warden_sigil"}
bosses = []
for i, (bid, b) in enumerate(BOSSES.items()):
    t = boss_text.get(b["name"], {})
    melee = re.search(r"Melee:\s*(\d+)", t.get("stats", ""))
    drops = []
    for d in t.get("Drops", []):
        m = re.match(r"^([\d-]+)x\s+(.*)$", d)
        if m:
            drops.append({"count": m.group(1), "id": by_name.get(m.group(2).lower(), ""), "name": m.group(2)})
    bosses.append({
        "id": bid, "name": b["name"], "health": b["health"], "melee": int(melee.group(1)) if melee else 0,
        "key": boss_keys.get(bid, ""), "summon": t.get("Summoning", []), "fight": t.get("The fight", []),
        "strategy": " ".join(t.get("Strategy", [])), "drops": drops, "image": f"img/bosses/{bid.split(':')[1]}.png",
        "order": i + 1,
    })

# ---------------------------------------------------------------- images
os.makedirs(os.path.join(OUT, "img", "items"), exist_ok=True)
os.makedirs(os.path.join(OUT, "img", "bosses"), exist_ok=True)
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)


def tex_map(json_name):
    d = read_json(find("Wildbloom_RP/textures/" + json_name))["texture_data"]
    out = {}
    for k, v in d.items():
        t = v["textures"]
        t = t[0] if isinstance(t, list) else t
        t = t["path"] if isinstance(t, dict) else t
        p = find("Wildbloom_RP/" + t + ".png")
        if p:
            out[k] = p
    return out


item_tex = tex_map("item_texture.json")
block_tex = tex_map("terrain_texture.json")
geos = {}
for path in rp(r"models/blocks/.*\.json$"):
    for g in read_json(path)["minecraft:geometry"]:
        geos[g["description"]["identifier"]] = g


def render_block(cubes, textures, size=128):
    """Isometric icon from Bedrock geometry cubes (per-face UV), one quad per texel, painter's order."""
    quads = []
    shade = {"up": 1.0, "south": 0.82, "east": 0.64}
    for c in cubes:
        (x0, y0, z0), (w, h, d) = c["origin"], c["size"]
        x1, y1, z1 = x0 + w, y0 + h, z0 + d
        uvs = c.get("uv", {})
        for face in ("up", "south", "east"):
            f = uvs.get(face)
            if not f:
                continue
            tex = textures.get(f.get("material_instance", "*")) or textures.get("*")
            if tex is None:
                continue
            (u0, v0), (uw, uh) = f["uv"], f["uv_size"]
            if face == "up":
                corner, du, dv, n = (x0, y1, z0), (1, 0, 0), (0, 0, 1), (abs(w), abs(d))
            elif face == "south":
                corner, du, dv, n = (x0, y1, z1), (1, 0, 0), (0, -1, 0), (abs(w), abs(h))
            else:
                corner, du, dv, n = (x1, y1, z1), (0, 0, -1), (0, -1, 0), (abs(d), abs(h))
            if n[0] == 0 or n[1] == 0 or uw == 0 or uh == 0:
                continue
            cols, rows = int(abs(uw)), int(abs(uh))
            su, sv = n[0] / cols, n[1] / rows
            for j in range(rows):
                for i in range(cols):
                    px = tex.getpixel(((int(u0) + i) % tex.width, (int(v0) + j) % tex.height))
                    if px[3] < 20:
                        continue
                    pts = []
                    for a, b in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)):
                        pts.append(tuple(corner[k] + du[k] * a * su + dv[k] * b * sv for k in range(3)))
                    cx = sum(p[0] for p in pts) / 4
                    cy = sum(p[1] for p in pts) / 4
                    cz = sum(p[2] for p in pts) / 4
                    col = tuple(int(px[k] * shade[face]) for k in range(3)) + (255,)
                    quads.append((cx + cy + cz, pts, col))
    quads.sort(key=lambda q: q[0])
    s = size / 16 * 0.47
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    cos30, sin30 = math.cos(math.pi / 6), 0.5

    def proj(p):
        x, y, z = p
        return (size / 2 + (x - z) * cos30 * s, size / 2 + 8 * s - y * s + (x + z) * sin30 * s)

    for _, pts, col in quads:
        dr.polygon([proj(p) for p in pts], fill=col, outline=col)
    return img


FULL_CUBE = [{"origin": [-8, 0, -8], "size": [16, 16, 16],
              "uv": {f: {"uv": [0, 0], "uv_size": [16, 16]} for f in ("up", "south", "east")}}]
for iid, it in items.items():
    short = iid.split(":")[1]
    dest = os.path.join(OUT, "img", "items", short + ".png")
    if it["kind"] == "item":
        key = None
        icon = read_json(find(f"Wildbloom_BP/items/{short}.json"))["minecraft:item"]["components"].get("minecraft:icon")
        if isinstance(icon, dict):
            key = icon.get("texture") or icon.get("textures", {}).get("default")
        elif isinstance(icon, str):
            key = icon
        p = item_tex.get(key) or find(f"textures/items/{short}.png")
        if p:
            image(p).resize((64, 64), Image.NEAREST).save(dest)
            it["icon"] = f"img/items/{short}.png"
        continue
    comps = it.pop("_components")
    geo = comps.get("minecraft:geometry")
    geo = geo if isinstance(geo, str) else (geo or {}).get("identifier", "")
    mats = {k: v.get("texture") for k, v in comps.get("minecraft:material_instances", {}).items()}
    if geo == "geometry.wb_cross":
        p = block_tex.get(mats.get("*"))
        if p:
            image(p).resize((64, 64), Image.NEAREST).save(dest)
            it["icon"] = f"img/items/{short}.png"
        continue
    textures = {k: image(block_tex[v]) for k, v in mats.items() if v in block_tex}
    if geo == "geometry.wb_pool_0":  # show pools full
        geo = "geometry.wb_pool_4"
        liq = mats.get("liq", "").replace("liq0", "liq4")
        if liq in block_tex:
            textures["liq"] = image(block_tex[liq])
    cubes = FULL_CUBE if geo == "minecraft:geometry.full_block" else [
        c for b in geos.get(geo, {}).get("bones", []) for c in b.get("cubes", [])]
    if cubes and textures:
        render_block(cubes, textures).save(dest)
        it["icon"] = f"img/items/{short}.png"

# boss portraits: front view (first column) of each row of the preview sheet
sheet = Image.open(BOSS_SHEET).convert("RGBA")
row_h = sheet.height // 3
for i, b in enumerate(bosses):
    crop = sheet.crop((0, i * row_h, sheet.width // 4, (i + 1) * row_h))
    crop.save(os.path.join(OUT, "img", "bosses", b["id"].split(":")[1] + ".png"))

# hero strip of flowers
flower_ids = [f["id"] for f in sorted(flowers, key=lambda f: f["tier"])]
strip = Image.new("RGBA", (16 * len(flower_ids) * 4, 64), (0, 0, 0, 0))
for i, fid in enumerate(flower_ids):
    p = os.path.join(OUT, "img", "items", fid.split(":")[1] + ".png")
    if os.path.exists(p):
        strip.paste(Image.open(p), (i * 64, 0))
strip.save(os.path.join(OUT, "img", "flower-strip.png"))

# stats the Lexicon builder generated (damage, durability, armor points, flask effects)
lexjs = zf.read(find("scripts/lexicon.js")).decode("utf-8")
m = re.search(r"/\*GEN\*/\s*(\{.*?\})\s*/\*END\*/", lexjs, re.S)
GEN = json.loads(m.group(1)) if m else {}

# ---------------------------------------------------------------- output
for iid, it in items.items():
    it["category"] = category(iid)
    it.setdefault("text", [])
    tool = GEN.get("tools", {}).get(iid)
    if tool:
        if tool.get("damage"):
            it["damage"] = tool["damage"]
        if tool.get("durability"):
            it["durability"] = tool["durability"]
    armor = GEN.get("armor", {}).get(iid)
    if armor:
        it["armor"] = armor.get("protection")
    if iid in GEN.get("flasks", {}):
        it["effect"] = GEN["flasks"][iid]
    if iid in TOOL_MAX_CHARGE:
        it["charge"] = TOOL_MAX_CHARGE[iid]
    if iid in BATTERY_CAP:
        it["charge"] = BATTERY_CAP[iid]
    if iid in POOLS:
        it["capacity"] = POOLS[iid]["cap"]
    elif iid in ACCEPTORS:
        it["capacity"] = ACCEPTORS[iid]

used = {i for r in recipes for i in r["ingredients"] + [r.get("station", "")]}
vanilla = {i: vanilla_name(i) for i in sorted(used) if i and not i.startswith("wb:")}

guides = []
for ch in chapters:
    guides.append({"title": ch["title"], "slug": ch["slug"], "intro": ch["intro"],
                   "sections": [{"title": re.sub(r"\s+T(\d)$", r" (tier \1)", s["title"]), "slug": s["slug"],
                                 "lines": s["lines"]} for s in ch["sections"]]})

# the add-on itself, for the Download button
os.makedirs(os.path.join(OUT, "download"), exist_ok=True)
download = f"download/Wildbloom-v{version}.mcaddon"
with open(os.path.join(OUT, download), "wb") as f:
    f.write(open(ADDON, "rb").read())

wiki = {
    "version": version,
    "download": download,
    "categories": [c for c in CATEGORY_ORDER if any(i["category"] == c for i in items.values())],
    "items": sorted(items.values(), key=lambda i: (CATEGORY_ORDER.index(i["category"]), i["name"])),
    "recipes": recipes,
    "vanilla": vanilla,
    "flowers": flowers,
    "helpers": helpers,
    "bosses": bosses,
    "enchantments": [{"rune": k, "enchants": [f"{e[0].replace('_', ' ').title()} {['', 'I', 'II', 'III', 'IV', 'V'][e[1]]}" for e in v]}
                     for k, v in ENCHANT_RUNES.items()],
    "pools": [{"id": k, "capacity": v["cap"], "overflow": v["overflow"]} for k, v in POOLS.items()],
    "guides": guides,
}
with open(os.path.join(OUT, "data", "wiki.json"), "w", encoding="utf-8") as f:
    json.dump(wiki, f, ensure_ascii=False, separators=(",", ":"))

missing = [i["id"] for i in items.values() if "icon" not in i]
print(f"Wildbloom v{version}: {len(items)} items/blocks, {len(recipes)} recipes, {len(guides)} guide chapters")
if missing:
    print("no icon:", ", ".join(missing))
no_text = [i["id"] for i in items.values() if not i["text"]]
if no_text:
    print("no lexicon text:", ", ".join(no_text))
