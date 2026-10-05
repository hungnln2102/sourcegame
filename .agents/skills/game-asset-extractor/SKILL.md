---
name: game-asset-extractor
description: >-
  Guidelines and automated workflows for reverse engineering Android APK/XAPK files, 
  extracting visual UI, character sprites, Spine animations, audio, maps, and decoding 
  ASTC/ETC textures into PNGs for Cocos, Unity, and HTML5 mobile games.
---

# Game Asset Extractor Skill

Use this skill whenever the user requests to extract, crawl, or reverse-engineer assets (banners, UI, character sprites, Spine animations, sound, voice, maps) from an APK, XAPK, or Cocos/Unity game package.

---

## Game Engine Inspection & Workflow Selection

Before extracting, inspect the APK/XAPK structure to identify the game engine:

### 1. Cocos Creator (UUID Mapping & ASTC Decoding)
- **Indicators:** Presence of `cc.config.*.json` or `config.*.json` containing `uuids` and `paths`.
- **Texture Format:** Often uses `.astc` files with header `13aba15c`.
- **Procedure:**
  1. Map Base64 UUIDs to standard UUID format (`8-4-4-4-12`).
  2. Map UUIDs to logical pathnames from `config.json`.
  3. Decode `.astc` raw bytes to PNG using `texture2ddecoder`.
  4. Save extracted assets preserving original folder structure (`ui/`, `actors/`, `audio/`, `maps/`, `spine/`).

### 2. Unity Engine (AssetBundle Unpacking)
- **Indicators:** Presence of `assets/bin/Data/` or `.bundle` files.
- **Procedure:**
  1. Use `UnityPy` Python library to parse asset bundles.
  2. Filter for `Texture2D`, `AudioClip`, `TextAsset`, and `Sprite`.
  3. Save exported assets to respective directories.

### 3. Web / HTML5 / Network-Streamed Games
- **Indicators:** APK contains minimal assets, network requests load assets dynamically from a CDN.
- **Procedure:**
  1. Inspect network endpoints or `list.txt` URL mappings.
  2. Use multi-threaded HTTP downloader (`downloadMapping.py`) to fetch assets.
  3. Unpack and clean resources locally.

---

## Preserved Tools & Scripts in Workspace

- **Web Tool Studio:** Located at `d:/Desktop/admin/sourcegame/web_tool/app.py`
  - URL: `http://127.0.0.1:5000`
- **Full Extract Script:** `export_all_assets_full.py`
