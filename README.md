# Wildbloom Wiki

The wiki for **Wildbloom**, a Minecraft Bedrock add-on of flower magic. It's a Blazor WebAssembly site,
deployed to GitHub Pages by `.github/workflows/deploy.yml` on every push to `main`.

Nothing in the wiki is typed in by hand. Items, blocks, recipes, flowers, bosses and the guide pages are all
generated from the add-on itself:

| File | What it is |
| --- | --- |
| `content/Wildbloom.mcaddon` | The add-on build. Names, recipes, flower stats, textures and block models come from here. |
| `content/lexicon.txt` | The in-game Lexicon text (`book-preview.txt` from the Lexicon tool). Becomes the guide pages and item descriptions. |
| `content/bosses.png` | Boss render sheet (front view of each boss is cropped for the Bosses page). |

## Updating for a new add-on version

1. Replace `content/Wildbloom.mcaddon` with the new build (keep the file name).
2. Replace `content/lexicon.txt` with the matching `book-preview.txt`.
3. Push to `main`. The workflow regenerates everything and redeploys.

## Running locally

Needs Python 3 with Pillow, and the .NET 8 SDK.

```sh
pip install pillow
python tools/build_wiki_data.py content/Wildbloom.mcaddon content/lexicon.txt content/bosses.png src/WildbloomWiki/wwwroot
dotnet run --project src/WildbloomWiki
```

## First-time GitHub Pages setup

In the repository's **Settings → Pages**, set **Source** to **GitHub Actions**.

## Layout

- `tools/build_wiki_data.py` reads the add-on and writes `wwwroot/data/wiki.json`, item icons (block icons are
  rendered from the block models), boss portraits and a downloadable copy of the add-on.
- `src/WildbloomWiki/Pages` has one Razor page per section: overview, items/blocks, item detail, flowers, bosses,
  recipes and Lexicon chapters.
- `src/WildbloomWiki/Components/GuideText.razor` turns Lexicon text into headings, lists and recipe cards, and links
  every item it mentions.
