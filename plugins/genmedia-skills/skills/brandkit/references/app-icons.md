# App icon platform files and the logo sting

Verified: 2026-09-20. Every size, format and safe zone below was read that day on the platform's own page and lives in `scripts/icon-targets.json` with its source URL; `brandkit.py icon-export` reads the numbers from that file, never from this page. A platform changed a rule → correct the JSON row and its `verified_on`, then this table. Never fill a gap from memory: the `unverified` list in the JSON says what nobody could read on an official page.

`brandkit.py` abbreviates `python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py"`.

## 1. One approved icon in, platform files out

The input is the approved `app-icon` SVG (made by `brandkit.py icon`, or a companion mark, `logo.md` section 5). The export splits it into its two ingredients, the plate colour and the untouched mark, renders the mark once to find where its ink really is, and nests that same geometry into every file. Nothing is generated, traced or redrawn per size; every PNG is a browser render of the same vectors.

```bash
brandkit.py icon-export genmedia-output/<slug>/logo/app-icon.svg --brand <slug> --name "<App Name>"
```

- With `--brand` the file must be the one approved in slot `app-icon` (`not_approved` otherwise); the export is attached to that slot, goes stale when the palette or logo revision changes, and `export-list --copy` carries the whole folder into `package/app-icon/`.
- Without `--brand` it is a plain converter for an icon the user brought: pass `--out-dir`. An SVG without a full-canvas plate needs `--background "#hex"`.
- `--platform ios|play|android|web|macos` (repeatable) limits the run; the default is all five. `--padding` (default 0.18) is the free margin around the mark's ink on the full-bleed files. About 15 to 20 seconds for everything.
- A raster icon cannot be split into plate and mark: ask for the SVG, or trace it first (`fal-ai/recraft/vectorize`, reviewed like any traced logo).

## 2. What is written

| Platform | Files under `genmedia-output/<slug>/app-icon/` | Rule the file follows | Source |
|---|---|---|---|
| iOS, iPadOS, App Store | `ios/AppIcon-1024.png` | 1024x1024, square and unmasked (the system rounds the corners), opaque, written WITHOUT an alpha channel. Xcode builds every other iOS size from this one image | Apple HIG "App icons"; Xcode "Configuring your app icon" |
| Google Play listing | `play/play-icon-512.png` | 512x512, 32-bit PNG with alpha, sRGB, at most 1024 KB, full square, no shadow: Play masks it at 30 percent radius | Play icon design specifications; Play Console Help 9866151 |
| Android launcher | `android/res/mipmap-<density>/ic_launcher_foreground.png` and `ic_launcher_monochrome.png` (mdpi 108 px to xxxhdpi 432 px), `mipmap-anydpi-v26/ic_launcher.xml` and `ic_launcher_round.xml`, `values/ic_launcher_background.xml` | layers 108x108 dp, logo between 48 and 66 dp, fitted to the 66 dp circle that no OEM mask clips; the plate is a colour resource; the monochrome layer feeds themed icons (Android 13 and later, alpha only) | Android "Adaptive icons"; `AdaptiveIconDrawable`; screen densities |
| Web | `web/favicon.ico` (16, 32, 48 px PNG entries), `favicon.svg`, `apple-touch-icon.png` (180, opaque), `icon-192.png`, `icon-512.png` (purpose `any`), `maskable-192.png`, `maskable-512.png`, `site.webmanifest`, `favicon-snippet.html` | maskable: ink inside the centred circle of radius 40 percent, no transparent pixels; `any` and `maskable` are separate files; Chrome's install criteria name 192 and 512 px | W3C Web App Manifest; web.dev install criteria and maskable icons; HTML Standard `rel=icon`; Google Search favicon guidelines |
| macOS | `macos/AppIcon.iconset/icon_<n>x<n>[@2x].png` for 16, 32, 128, 256, 512; `macos/AppIcon.icns` when `iconutil` exists | Apple's iconset names; 512@2x replaces a 1024 file; rounded corners on a transparent ground, because an `.icns` is shown as drawn on older systems | Apple asset catalog "Icon Set Type"; High Resolution guide |
| Review | `icon-sheet.png`, `icon-sheet.html`, `icon-export.json` | true pixel sizes 256 to 16 on light and dark, then the Play mask, a circular adaptive mask and the maskable safe circle; the JSON lists every file with size, alpha, bytes, hash, the rules and their URLs | |

Favicon strategy: all web files go to the site root. `/favicon.ico` stays for crawlers and old browsers (the HTML Standard makes it the fallback when no link is declared, and Google Search lists ICO but not SVG); the SVG is declared last because the last of several equally fitting icons wins. Paste `favicon-snippet.html` into `<head>` and merge the `icons` member of `site.webmanifest` into the site's own manifest.

Not written, and what to say: Apple's layered Icon Composer file (made in Apple's tool from the SVG mark; the system also derives dark, clear and tinted looks from a flat icon by itself), legacy Android launcher PNGs for API 25 and lower, Windows tiles, a vector drawable (Android Studio's Vector Asset tool converts `favicon.svg`). Dark or tinted iOS variants on request: `svg-variants` plus `png` give a mark on a transparent ground; the user places them in Xcode.

## 3. Checks, and what to do about them

The command exits 1 and attaches nothing while `problems` is not empty.

| Code | Meaning | Do |
|---|---|---|
| `wrong_size`, `alpha`, `no_alpha` | a render came back in another size, or with or without the alpha channel the platform wants | run again; repeated → `troubleshooting-brandkit.md` |
| `bytes_over_cap` | the Play icon is over 1024 KB | a mark that heavy is a texture, not a symbol: simplify it (new candidate) |
| `clipped_by_mask` | adaptive foreground ink lies beyond the 36 dp masked viewport | the mark is far from compact; use a symbol-only mark |
| `outside_safe_circle` (problem, maskable) | ink beyond the 40 percent circle | same; the fit normally prevents it |
| `outside_safe_circle` (warning, Android) | ink between the 33 dp safe circle and the 36 dp viewport: corners of a blocky mark that a round OEM mask may touch | look at "adaptive, circle" on the sheet; say so, or use a rounder mark |
| `mark_not_compact` | the ink is much wider than tall or the reverse | a lockup in a square is unreadable: symbol only |
| `icns_not_made` | no `iconutil` (not macOS) | deliver the iconset; `iconutil -c icns AppIcon.iconset` on a Mac finishes it |
| `icon_empty` | the mark rendered to nothing | open the SVG; an empty file or an opaque full-canvas shape that is not a plate |

Then LOOK: Read `icon-sheet.png`. At 32 and 16 px the mark must still be one recognisable shape on both grounds; if not, say it and offer a simpler symbol for the small sizes instead of shipping mush. Read `ios/AppIcon-1024.png` once for colour and centring.

Store content rules travel with the icon: no ranking, price, deal or store-category text or badges on it (Play states this for the icon; Apple keeps such claims out of listing assets too).

## 4. Hand-off wording

```
App icon files: genmedia-output/<slug>/app-icon/
iOS and App Store: ios/AppIcon-1024.png (drop into the AppIcon well; Xcode builds the rest) · Google Play: play/play-icon-512.png
Android: android/res/ (copy into app/src/main/res; adaptive foreground, monochrome, plate colour, XML) · macOS: macos/AppIcon.iconset <+ AppIcon.icns>
Web: web/ (copy to the site root, paste favicon-snippet.html into <head>, merge site.webmanifest)
Made from the approved icon without redrawing; sizes and safe zones as published by each platform on <verified_on>. Checked: sizes, alpha, safe circles; small sizes on icon-sheet.png.
```

Other skills take the icon from here: `launch-graphics` reads `app.icon` from `web/icon-512.png` or the approved `app-icon.svg`.

## 5. Logo sting

A 2 to 3 second reveal of the approved mark for video intros and end cards. The honest path, verified 2026-09-20 on Chrome plus ffmpeg: every frame is the real SVG nested under a transform, an opacity or a clip and rendered by the browser; ffmpeg joins the frames. A video model never touches the logo: it would redraw it.

```bash
brandkit.py sting genmedia-output/<slug>/logo/logo-primary.svg --brand <slug> --out genmedia-output/<slug>/logo/sting-1080x1920.mp4 --background "#1f3d2b" --size 1080x1920 --style rise
```

- Styles: `rise` (fade, slight lift and settle), `pop` (scale with a small overshoot), `wipe` (left to right reveal). The reveal takes 0.9 s, the rest of `--seconds` (default 2.5) holds the finished logo. `--size` is the video's size (`1920x1080`, `1080x1920`, `1080x1080`), `--span` the logo's share of the width (default 0.5).
- Pick the variant that reads on the ground: the primary mark on a light palette colour, `reversed` on a dark one. With `--brand` the file must be the approved logo or one of its registered variants.
- Output: H.264 MP4, silent, plus `<name>-last.png` (the held frame, usable as a still end card). `--keep-frames` keeps the PNG sequence. About 15 seconds per clip.
- Needs a browser and a local ffmpeg (`tools` → `can.sting`). Missing → `tool_missing`: say the sting was not made here; do not route the logo through a video model instead.
- Look before delivering: Read `<name>-last.png`, and say that the clip is silent (a sound logo is an `audio` job).
