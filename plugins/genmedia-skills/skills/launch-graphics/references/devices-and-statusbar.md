# Devices and status bars

What `scripts/devices.json` holds, how `launchkit.py` decides what to do with the status bar of a capture, how you decide `statusbar_state` by looking, how to get a clean capture in the first place, how a user brings their own bezels, bars and fonts, and the credit the shipped bars ask for. The decision table is the script's (`lk1`) and is unit-tested row by row; the store rules behind it are in `store-policy.md` (Verified: 2026-09-20). `launchkit.py` abbreviates the call shown in SKILL.md.

## 1. `devices.json`

Dated data, no code (`verified_on`). Frames are drawn from these numbers as HTML and CSS; no device bitmap ships with the skill. The file belongs to the skill: in a user's session it is read, never edited.

| Block | Entries | Numbers |
|---|---|---|
| `frames` | `iphone`, `ipad`, `android-phone`, `android-tablet`, `neutral-phone`, `browser`, `macos-window`, `none` | `kind` (`phone`, `tablet`, `window`, `none`), `os` (`ios`, `android`, `neutral`, `desktop`), `generation`; `bezel`, `rim`, `body_radius` as fractions of the body width; `screen_radius` and `cutout` (`type` `island`, `punch` or `none`, `w`, `h`, `top`) as fractions of the screen's short side; `statusbar` and `bottombar` (bar ids or null); `buttons`; `colors`. Windows carry `titlebar` (height as a fraction of the window width with a pixel minimum, dot colours for a light and a dark bar, the address `pill` or `title: true`) |
| `bars` | status: `ios`, `ipad`, `android`, `android-tablet`, `neutral`; bottom: `ios-home`, `ipad-home`, `android-gesture`, `android-tablet-gesture`, `neutral-bottom` | `height` as a fraction of the screen's short side; status bars: `time`, `layout` (positions and sizes of time and icon cluster, icon `order`, `glyph_ref`, `gap_before`, font stack), `glyphs` (SVG path data), `glyph_boxes`, `glyph_origin` per glyph; bottom bars: `pill` (`w`, `h`, `bottom`) or null. A bar that ships as artwork also has `svg` (the markup), optionally `svg_landscape` (a landscape artboard: the iPad bars), `svg_includes_time` (status bars), `origin`, `license`, `changes`. Phone status bars carry `landscape` (section 3): `height` and `center_y` for Android, `hidden: true` for iOS and neutral, with `why`, `source` and `verified_on` |
| `screens` | `ios`, `android` | known full-screen pixel sizes; `capture add` and `probe` use them for `fullscreen_match` (exact, or within 1 percent of the aspect, either orientation) |

- **Generation labels name a class, not a model**: "current iPhone class with a Dynamic Island pill (generic drawing, no vendor artwork)", "current Pixel-class Android phone with a centred punch-hole". Say "an iPhone-style frame", never a model name: the drawing is generic on purpose.
- **What ships, and whose it is.** Six bars ship as `svg` exported directly from the "Assets Kit UI Mobile, Tablet & Desktop" by Julien Fovelle (Figma Community file 1127262460074722420, `license: "CC BY 4.0"`, read on the file page 2026-09-22): the status bars `ios`, `ipad` (portrait and `svg_landscape`) and `android`, the home indicators `ios-home` and `ipad-home` (portrait and landscape) and the `android-gesture` pill. The kit has no Android tablet bars, so `android-tablet` and `android-tablet-gesture` are adapted for this project from the phone exports (camera hole removed, 800 dp artboard with 16 dp side padding, 36 dp tall; the same 108 x 4 dp pill) and carry the same origin and licence. `changes` records what was done (exported with small adjustments, recoloured at render time). Every status bar carries its clock as outlines (9:41 on iOS, 9:30 on Android). `origin` names third-party artwork only; the `neutral` bars are this project's. The drawn `glyphs` stay in the file as the fallback (`glyph_origin: "drawn for this project"`). Section 7 says what the licence asks of you.
- **Order of precedence per bar:** an imported asset (section 6) → the bar's shipped `svg` (`svg_landscape` on a landscape screen when present) → the glyphs drawn for this project. Imported and shipped SVG bars render through the same path; every bar takes its colour from the strip.
- **Cut-outs are the frame's job.** The Dynamic Island in the iPhone export and the camera hole in the Android export cross the middle of the artboard and are dropped at render time (section 6, rule 3); the drawn `iphone` frame paints its own island, `android-phone` its punch-hole, both on the left short side in landscape; tablets and `neutral-phone` have none. A real capture never contains the island or the hole (they are hardware), so nothing is doubled. Frameless pages show no cut-out.
- **Bar heights** are device measures over the screen's short side: iPhone 62 pt on 402 pt (0.1542), iPad 32 pt on 1032 pt (0.031), Android phone 52 dp on 412 dp (0.1262), Android tablet 36 dp on 800 dp (0.045). Home indicators: iPhone 34 pt (0.0846), iPad 21 pt (0.0203), Android gesture 24 dp on a phone (0.0583) and on a tablet (0.03).
- **A yearly device change is a data edit** by the skill's maintainers, not a code change. Re-measure on a real full-screen capture of the new device and OS: the new sizes for `screens` (from the store's screenshot specification), the bar `height` (bar height over screen width), `cutout.w`, `h`, `top`, `bezel` and `screen_radius`, the `layout` positions (`time_x`, `cluster_x`, `center_y`, `time_size`, `glyph_h`), the bottom `pill`, and a fresh export of any shipped `svg` with its `origin`, `license` and `changes`; then the `generation` text and `verified_on`. The tests check that every frame's bars exist.

## 2. What the bar work looks like

| Action | What the page does |
|---|---|
| `extend` | the screen grows: a strip on top in the colour of the capture's top edge with time and glyphs, a strip below in the colour of its bottom edge with the home indicator or gesture pill. The capture is neither covered nor scaled |
| `extend_blank` | the same two strips, empty: no time, no glyphs, no pill |
| `overlay` | time and glyphs are drawn over the capture's own, empty bar area; nothing is added below |
| `repaint` | the bar area is covered with its own flat colour, then time and glyphs are drawn on it |
| `repaint_blank` | the bar area is covered and left empty |
| `mask` | the user's yes to cover a non-standard bar: like `repaint` (or `repaint_blank` in `universal`), whether the bar area is flat or not; reported as `repaint` or `repaint_blank` |
| `keep` | the capture stays as it is |
| `none` | no bar work at all |

`metrics.statusbars[]` of every file reports `capture`, `state`, the final `action` and the sampled `strip` colour.

## 3. The decision table

No bar work (`none`), whatever the state: `statusbar: "none"`; window frames; `web` and `desktop` captures under `statusbar: "auto"`; `ph-thumbnail`. `statusbar: "keep"` → `keep`, without a warning, in every mode. `statusbar: "mask"` (only after the user said yes, section 4) → `mask`: the capture's own bar area is covered with its most common colour, flat or not, and the frame's bar is drawn on it (left blank in `universal`); the page reports `repaint` or `repaint_blank`, no warning. A `missing` capture under `mask` is treated as under `auto`.

Under `statusbar: "auto"`:

| Mode and frame | `statusbar_state` | Action | Warning |
|---|---|---|---|
| `app-store`, `play`, `both` with an iOS or Android frame, or frameless on a store target | `missing` | `extend` | - |
| | `empty` | `overlay` | - |
| | `dirty` | bar area flat → `repaint`; not flat → `keep` | `statusbar_kept_dirty` when kept |
| | `clean`, capture OS = frame OS | `keep` | - |
| | `clean`, capture OS ≠ the drawn bar's OS (an iOS capture in the Android frame, or frameless on a Play target, and the reverse) | flat → `repaint` with that bar; not flat → `keep` | `statusbar_os_mismatch` when kept |
| `universal`, or a `neutral-phone` frame in any mode | `missing` | `extend_blank` | - |
| | `empty`, `clean`, `dirty` | flat → `repaint_blank`; not flat → `keep` | `statusbar_identifies_os` when a `clean` or `dirty` bar is kept; none for `empty` |

- The bar drawn is the **page's**, never the capture's own: an `android-phone` frame draws the Android bar at 9:30 even over an iOS capture. With `frame: "none"` a phone capture borrows the bars of the target's own store (`appstore-*` → iOS, `play-*` including `play-feature` → Android), so the row above applies to a frameless capture too: an iOS capture on a Play target is repainted with the Android bar when flat, kept with `statusbar_os_mismatch` when not. Off-store targets (`og`, `x-card`, `ph-*`, `ad-*`) borrow the capture's own OS, `universal` the neutral bars.
- **Flat** is measured in the page on the capture's own bar area (15.4 percent of the short side on an iPhone-shaped capture, 12.6 on an Android phone, 3.1 on an iPad, 4.5 on an Android tablet): at least 78 percent of the pixels within a small tolerance of the most common colour, and the lowest rows and a narrow column at each side edge (1.2 percent of the width, so a tablet's clock and icons near the edges do not spoil it) almost entirely so. A plain bar with a clock and icons passes; a photo, a map or a gradient under the bar does not.
- **A phone capture in landscape** (a phone frame, or frameless with a phone-shaped capture; tablets keep their own bars and the iPad's `svg_landscape`). Verified 2026-09-23:
  - **Android** shows a status bar in landscape, 24 dp tall: `status_bar_height_landscape` is `status_bar_height_portrait` (24dp), and `SystemBarUtils` takes the larger of the top cutout inset and 24 dp, while a punch-hole on the short side adds no top inset (AOSP `android16-release` and `android17-release`, `core/res/res/values/dimens.xml` and `core/java/com/android/internal/policy/SystemBarUtils.java`). So the table above applies unchanged with `bars.android.landscape`: `extend` adds a 24 dp strip on top and the 24 dp gesture strip below, `overlay` and `repaint` draw over the capture's own 24 dp band. The artwork keeps its portrait scale (clock and icons are as large as in portrait) and moves up so its glyphs centre on the thinner strip; the drawn fallback glyphs move the same way. An imported `android` bar is placed the same way, so export it at 52 dp as for portrait.
  - **iOS** shows none: by default UIKit hides the status bar of a view controller in a vertically compact environment, which is every iPhone in landscape (https://developer.apple.com/documentation/uikit/uiviewcontroller/prefersstatusbarhidden). `bars.ios.landscape` is `hidden`, and so is the neutral bar, since one of the two platforms shows none. Rows under `hidden`: `missing` → `none` (no strip, no home indicator); `empty` → `keep`; `clean` of the page's own OS → `keep`; `dirty`, a `clean` bar of the other OS (an Android capture on an App Store page) or any bar in `universal` → flat: `repaint_blank`, not flat: `keep` with `statusbar_kept_dirty`, `statusbar_os_mismatch` or `statusbar_identifies_os`; `mask` → `repaint_blank`. An iPhone capture in landscape has no bar of its own, so it gets no bar work at all.
- All three warnings carry the same advice: a clean capture (section 5), or a capture per OS through the slide's capture map (`templates.md` section 1).

## 4. Deciding `statusbar_state`: look at the capture

`capture add` guesses `clean` for a full-screen match and `missing` otherwise. Read every capture and correct the guess in `deck.json`.

| State | What you see | Typical source |
|---|---|---|
| `missing` | app content starts at the very top edge: no clock, no icons, no empty band. `fullscreen_match` is usually null | cropped captures, design exports, web views, captures from a tool that cuts the bars off |
| `empty` | full-screen size; a band in the app's ground colour at the top with nothing in it | captures taken with the bar hidden, full-screen apps and games |
| `dirty` | any of: a carrier name, a battery that is not full or is charging, weak signal or Wi-Fi, notification icons next to the clock (Android), alarm, location, recording, VPN or do-not-disturb marks, a "back to app" breadcrumb (iOS), a clock that differs from the other slides | a capture from a phone in daily use |
| `clean` | clock, full signal, full Wi-Fi, full battery and nothing else. iOS: clock on the left of the island, icons on the right. Android: clock at the left, icons at the right, no notification icons | simulator or emulator with overrides (section 5) |

- A bar that is clean but shows another time than the rest of the set: mark it `dirty`.
- **A `dirty` bar is the user's call.** Before the first compose, ask once for all dirty captures together (Q3 of the skill's question budget): "The status bar in <captures> is not standard (<what you saw: 14:27, 62 percent battery, carrier name>). A: mask it with the standard bar (9:41 / 9:30, full icons) · B: keep it as it is." A → `statusbar: "mask"` on those captures; B → `statusbar: "keep"`. Say that a mask over a photo or gradient becomes a flat band in the bar's main colour. Silence is not a yes: without an answer keep `auto` (flat bars are repainted, others kept with `statusbar_kept_dirty`) and say so in the delivery.
- A capture cropped only at the top still has its own home indicator: `extend` would add a second one. Crop both ends, or retake.
- Bottom bars are only ever added by `extend`. In every other state the bottom of the capture is left alone.

**Glyph colour** comes from the strip: most common colour of the bar area, relative luminance below 0.36 → white time and glyphs, otherwise black. The pill takes its colour from the bottom strip the same way.

**Times**: `9:41` on iOS bars, `9:30` on Android bars (`bars.<id>.time`), all icons full. Neither store names a time; one fixed time per platform keeps a set consistent. Both are the clocks the shipped exports carry as outlines and the values of the capture overrides in section 5. What the stores do ask for: Apple's marketing guidelines want a full network icon, a full Wi-Fi icon and a full battery icon; Google's preview asset guidance wants no carrier name and no notifications, with battery, Wi-Fi and cell icons full (`store-policy.md` sections 3 and 5). The times are not localized. The shipped bars carry their clock as outlines; only the drawn fallback glyphs set the time as live text in the system UI font of the machine that renders.

## 5. Clean captures at the source

iOS simulator (run on an iPhone 17 Pro and an iPhone SE (3rd generation) simulator, iOS 26.5, on 2026-09-23; flags from `xcrun simctl status_bar`; `booted` stands for the running simulator, and a UUID from `xcrun simctl list devices booted` works too):

```bash
xcrun simctl status_bar booted override --time "9:41" --dataNetwork wifi --wifiMode active --wifiBars 3 --cellularMode active --cellularBars 4 --batteryState discharging --batteryLevel 100 --operatorName ''
xcrun simctl io booted screenshot home.png
xcrun simctl status_bar booted clear
```

Result on both: 9:41, full Wi-Fi, full cell signal, a full battery without a bolt, no carrier name.

- **`--batteryState discharging` with `--batteryLevel 100`** draws the plain full battery.
- **`--operatorName ''` removes the carrier name.** A home-button iPhone draws "Carrier" next to the signal bars unless it is set; a Dynamic Island iPhone draws no carrier name either way.
- **The clock follows the simulator's region, not the `--time` text.** `--time` is parsed as a time (free text such as `9:41 AM` is refused), then drawn in the region's format. A new simulator takes the Mac's region; with a 24-hour region (`en_TR` on the test Mac) the bar reads 09:41. Switch the region and reboot the simulator, then override again; the language list is left alone, but numbers and dates inside the app follow the new region too:
  ```bash
  xcrun simctl spawn booted defaults write -g AppleLocale en_US
  xcrun simctl shutdown booted
  xcrun simctl boot <UUID>
  ```
  Restarting SpringBoard alone did not change the clock. A home-button iPhone then shows `9:41 AM`.
- Ranges: `--wifiBars` 0 to 3, `--cellularBars` 0 to 4, `--batteryLevel` 0 to 100.

Android demo mode (run on a Pixel 9 Pro emulator, Android 16, API 36, build BE2A.250530.026.D1, on 2026-09-23; extras checked the same day against the SystemUI source on AOSP `android16-release` and `android17-release`; check the screen before capturing):

```bash
adb shell settings put global sysui_demo_allowed 1
adb shell am broadcast -a com.android.systemui.demo -e command enter
adb shell am broadcast -a com.android.systemui.demo -e command clock -e hhmm 0930
adb shell am broadcast -a com.android.systemui.demo -e command battery -e level 100 -e plugged false -e powersave false -e defender false
adb shell am broadcast -a com.android.systemui.demo -e command network -e wifi show -e level 4 -e fully true
adb shell am broadcast -a com.android.systemui.demo -e command network -e mobile show -e slot 99 -e level 4 -e datatype none
adb shell am broadcast -a com.android.systemui.demo -e command notifications -e visible false
adb exec-out screencap -p > home.png
adb shell am broadcast -a com.android.systemui.demo -e command exit
```

Result on that emulator: 9:30, full Wi-Fi, full cell signal without a data type label, a full battery without a bolt, no notification or system icons.

- **`-e fully true` removes the Wi-Fi exclamation mark.** The demo Wi-Fi counts as validated only when `fully` is `true`; without it the icon shows "connected, no internet".
- **`-e slot 99` removes the 3G label.** Without `slot` the demo SIM takes subscription ID 1. When the device's own SIM also has ID 1 (the emulator's does), SystemUI keeps drawing the real connection under demo mode: the real data type (3G on the emulator) and the real signal, whatever `level` and `datatype` say. Any ID the device's SIM does not use works; if the cell icon still ignores `level` or shows a label, pick another number.
- **`-e datatype none` is needed.** Any value SystemUI does not know draws no label; leaving `datatype` out falls back to 3G.
- **Other marks.** Entering demo mode hides the real system icons (do not disturb was hidden on the emulator), so no `status` command is sent; that command only adds icons. Roaming shows only with `-e roam show`. The demo battery keeps the device's saver and battery-defender state unless `powersave false` and `defender false` are sent.

These commands are for the user to run; the skill's permissions do not cover them. A user without a simulator: crop the bar off at both ends and set `missing`, or accept the repaint.

Sources: https://android.googlesource.com/platform/frameworks/base/+/refs/heads/android17-release/packages/SystemUI/docs/demo_mode.md and, in the same tree, `packages/SystemUI/src/com/android/systemui/statusbar/pipeline/wifi/data/repository/demo/DemoModeWifiDataSource.kt`, `.../pipeline/mobile/data/repository/demo/DemoModeMobileConnectionDataSource.kt` and `DemoMobileConnectionsRepository.kt`, `.../pipeline/mobile/domain/interactor/MobileIconsInteractor.kt`, `packages/SystemUI/src/com/android/systemui/statusbar/policy/BatteryControllerImpl.java` (AOSP `main` on googlesource stopped at March 2025; current code is on the release branches) · https://developer.android.com/tools/adb (screencap) · https://developer.apple.com/app-store/marketing/guidelines/ (status bar).

## 6. User-imported assets

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" assets import --kind bezel --name iphone --file "<path to the bezel PNG>"
python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" assets import --kind bezel --name iphone --file "<opaque bezel PNG>" --screen 60,58,1206,2622 --screen-radius 150
python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" assets import --kind statusbar --name ios --file "<path to the bar SVG>"
python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" assets import --kind statusbar --name ipad --device tablet --file "<path to the iPad bar SVG>"
python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" assets list
```

Flags: `--kind bezel|statusbar|bottombar|font`, `--name`, `--file`, `--os ios|android`; for bars `--device phone|tablet` (default `phone`); for bezels `--screen x,y,w,h`, `--screen-radius <px>` and `--opaque` (all in pixels of the bezel image). Files are copied to `.genmedia/launch-graphics/assets/<kind>/<name>.<ext>` with an entry in `index.json`, which keeps the source file's name, never its path; a second import under the same name replaces the first. They stay in the user's project: never copy them into the skill or a repository. An imported asset wins over the drawn one.

| Kind | File | Matched by | Notes |
|---|---|---|---|
| `bezel` | PNG or WebP | `--name` = frame id (`iphone`, `ipad`, `android-phone`, `android-tablet`, `neutral-phone`), or `<frame id>-portrait` / `<frame id>-landscape`, which wins for a capture of that orientation | two kinds, below. The index records `orientation` from the image; a bezel is never rotated, so a bezel of the other orientation leaves the drawn frame and a `note`. Used only when the screen's aspect is within 2 percent of the capture's screen (strips included); otherwise the drawn frame is used and the file carries a `note`. No shadow is added unless the set or slide says `bezel_shadow: true` |
| `statusbar` | SVG | `--name` = bar id (`ios`, `ipad`, `android`, `android-tablet`); else a bar imported with the same `--os` and the same `--device` class | replaces the shipped or drawn bar wherever the table says glyphs are drawn. The answer carries `viewbox: [w, h]`, and a `note` when the artboard is less than 5 times as wide as tall (probably not a whole status bar) |
| `bottombar` | SVG | `--name` = bottom bar id (`ios-home`, `ipad-home`, `android-gesture`, `android-tablet-gesture`); else `--os` inside the same `--device` class | replaces the pill inside the strip `extend` adds: scaled by height to that strip, centred, coloured like the pill would have been |
| `font` | `.woff2`, `.woff`, `.ttf`, `.otf` | `--name` = the family named in `theme.font.family`, when the deck lists no `files` | embedded as a data URI |

Bars are matched by **bar id**, not by frame id: an asset named `iphone` is never picked up as a bar. The `--os` fallback stays inside one device class (tablet frames take `--device tablet` bars, every other frame `phone` bars), so a phone bar never lands on a tablet frame. Simplest: name each file by its bar id.

**Two kinds of bezel.**

1. **Transparent screen hole** (the usual product bezel): the hole is found in the page (largest enclosed transparent area, at least 15 percent of the image; `screen_from: "detected"`), or named with `--screen` when detection misses it. Detection also measures the hole's corner radius and stores it as `screen_radius`: the capture is clipped to it, or its square corners would show outside the rounded body of the device (`--screen-radius` overrides the measurement). The bezel lies over the capture, so its own island or notch and its rounded screen corners stay visible.
2. **Opaque** (`opaque: true` in the answer): a file without alpha, or `--opaque` for an alpha PNG whose screen area is filled (detection answers `no_screen_hole` for it; `--screen` without `--opaque` would put the capture under the filled screen). `--screen x,y,w,h` is required (without it a file without alpha fails with `no_screen_hole`). The capture is drawn ABOVE the bezel inside that rectangle and clipped to `--screen-radius` (default 0: square corners, so measure the radius). Whatever the bezel paints inside the rectangle, a camera island included, is covered by the capture. The image's own background and outer corners show as they are: the answer's `note` recommends a PNG that is transparent outside the device.

**Apple's Product Bezels** are downloaded by the user from Apple Design Resources (https://developer.apple.com/design/resources/#product-bezels, layered and PNG files per device, seen 2026-09-20). This skill never ships, fetches or redistributes them. Apple's marketing guidelines ask that product images are used as they are: no added reflections, shadows or highlights, no cropping, tilting or obstructing. So an imported Apple bezel belongs on a layout that shows it whole and upright (`device-center`, or `bleed: false`), with no front decor over it and without `bezel_shadow`: by default the compositor adds no shadow, reflection or highlight to an imported bezel. You may say exactly that ("Apple's own bezel, whole, upright and unmodified"); never call a set compliant or promise a review outcome. Apple's PNG exports do have a transparent screen area; imported end to end on 2026-09-23 (2x PNGs exported from Apple's Figma file):

| Export | Size | Detected screen | Corner radius | Fits |
|---|---|---|---|---|
| iPhone 18 Pro | 900x1840 | 48,46,804,1748 | 126 | every current iPhone capture, 1179x2556 to 1320x2868, by the 2 percent rule; composed with 1206x2622 and 1320x2868 |
| iPhone 18 Pro Max | 980x2000 | 50,44,880,1912 | 126 | the same |
| iPhone Air | 920x1920 | 40,48,840,1824 | 126 | the same |
| iPhone Duo | 2062x1498, landscape | 80,80,1902,1338 | 109 | no store capture size (aspect 1.42) |
| iPad Pro M4 13" | 3000x2300, landscape | 124,118,2752,2064 | 62 | 2752x2064 landscape captures only |
| iPad Pro M4 11" | 2640x1880, landscape | 110,106,2420,1668 | 62 | 2420x1668 landscape captures only |
| iPad mini | 2550x1780, landscape | 142,146,2266,1488 | 44 | 2266x1488 landscape captures only |

The island of the iPhone exports stays visible over a simulator capture (1206x2622, iPhone 17 Pro, iOS 26.5) and sits on the capture's own island. The iPad exports are landscape: a portrait iPad capture keeps the drawn frame; export the portrait bezel and import it as `ipad-portrait` to have both. An iPad capture only fits the export of its own model: the three screens differ by more than 2 percent. A Samsung Galaxy S25 Ultra frame (1967x4106, not Apple's) paints a checkerboard into its screen, so detection answers `no_screen_hole`; `--opaque --screen 55,50,1842,3995 --screen-radius 80` (measured on that export) fits a 1440x3120 capture on `android-phone`, and the capture covers the frame's camera hole.

**Apple's own UI-kit bars are never shipped with this skill** (the shipped iOS bars come from the CC BY 4.0 kit above): the Apple Design Resources licence (dated 2023-06-21, https://developer.apple.com/support/downloads/terms/apple-design-resources/Apple-Design-Resources-License-20230621-English.pdf, read 2026-09-20) grants their use for mock-ups of software that runs on Apple's platforms and rules out embedding them in software or other products, redistributing, extracting and modifying them. A user may import their own export with `assets import` for the listing images of their Apple-platform app.

**How an imported bar is placed** (the export spec follows from it):

1. **Height wins.** A status bar is scaled so its artboard height equals the frame's bar height (`bars.<id>.height` x the screen's short side); the width follows the artboard. An artboard whose aspect implies another bar height is not corrected: a bar that looks too big or too small was exported at the wrong height. Export the bar at the heights of section 1 (62 pt, 32 pt, 52 dp, 36 dp).
2. **Two halves, flexible middle.** The bar is rendered twice, each copy clipped to its own half (each at most half the screen, at most half the artboard): the left half is pinned to the left screen edge, the right half to the right edge. An artboard of exactly the screen's point width joins seamlessly; a wider one (an iPad bar exported at landscape width, used on a portrait tablet) loses its empty middle; a narrower one gets a wider gap. Time and icons keep their distance to the edges in every case.
3. **Whatever crosses the middle is dropped**: an island, a camera hole or a background in the export would be split by the two halves, and the frame draws its own cut-out anyway. The test is per shape (`path`, `rect`, `circle`, `ellipse`): so keep the left cluster and the right cluster as separate shapes and never flatten a whole bar into one compound path, or all of it goes.
4. **A bottom bar** is scaled by height to the bottom strip and centred. A full-width navigation bar and a bare pill with its padding both work. Nothing is dropped here, so leave a background rectangle out: it would be painted as a solid block.
5. **One colour.** Every fill and stroke, as an attribute or in a `style`, becomes `currentColor`, and the page sets `color` from the strip (dark strip → white). `none` and `transparent` stay, opacities survive, shapes inside `clipPath`, `mask` and `defs` keep their paint, and ids are prefixed per copy so clip paths and masks still resolve. Two-tone details therefore need opacity, not a second colour.
6. **Time as outlines** (9:41 or 9:30). Live text would depend on the fonts of the rendering machine.
7. **Safety screen** (`svg_unsafe`, `svg_invalid`, `svg_too_large`): UTF-8 text up to 8 MB; no `script`, `foreignObject`, `image`, `use`, animation elements, event handlers, entity declarations, external `href` or `url()`. A `viewBox`, or numeric `width` and `height`, is required.

One SVG per bar and device class, named by bar id; `--device tablet` for tablet bars.

## 7. Credit for the shipped bars

CC BY 4.0 asks for credit. The script carries it for you, and you keep it attached:

- `launchkit.py specs` answers `attributions: [{origin, license, bars, changes}]`: everything third-party that ships in `devices.json`.
- The `proof.json` of every page whose plan drew a shipped bar carries `attributions: [{bar, origin, license, changes}]`. Pages that used an imported bar, the drawn fallback glyphs or no bar (kept or blank bars) have none.
- When you hand files on, the proofs go with them, and the delivery note says once: "Status bars and home indicators: Assets Kit UI Mobile, Tablet & Desktop by Julien Fovelle, CC BY 4.0." A user who publishes the images should credit the kit where that is practical (a credits page, the repository, the press kit). A user who imports their own bar replaces the artwork, and the credit no longer applies to those pages.
