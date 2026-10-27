# Getting a recording worth cutting

Read when the user has no recording yet, when a recording is unusable, or when a retake is cheaper than any edit. Hand these to the user in their own language, as a short list — never all of it at once.

## 1. What cannot be fixed afterwards

| Problem in the recording | Why no edit saves it |
|---|---|
| Too small (a 1280x720 window for a 1920x1080 demo) | upscaling a UI makes the text mushy; every zoom makes it worse |
| Someone's real data on screen | blurring looks like a cover-up and often misses a frame |
| A notification banner | it is in the pixels; cropping it away moves the whole frame |
| A wrong or empty UI state | the product has to be in the state the story needs |
| A cursor that never rests | there is nothing to cut to; the eye cannot follow |
| Baked-in letterboxing | bars inside bars, unless the content rectangle is cropped back out |

The answer to all of them is one more recording. It takes the user three minutes and saves an hour of editing.

## 2. Before recording

- **Record bigger than you deliver.** 2x (Retina) or at least 1.5x the delivery size, so a zoom still has pixels. A 9:16 store preview from a 1290x2796 phone recording is ideal; a desktop demo delivered at 1920x1080 should be captured at 2560x1440 or a 1920 window on a Retina screen.
- **Frame rate:** 60 fps if the tool offers it (scrolling looks better), delivered at 30. The App Store caps previews at 30 fps.
- **Demo data.** A seeded account with believable, harmless content: names that are obviously fictional, no customer e-mail addresses, no invoices, no API keys, no internal URLs.
- **Silence the machine.** Do Not Disturb / Focus, quit chat apps, hide the dock and the menu-bar clutter, close other tabs, turn off auto-updating widgets.
- **Set the window size** before recording (a fixed 1920x1080 window beats a full screen you will crop), zoom the browser to 100 %, and hide bookmarks bars and extension icons.
- **Slow the cursor down.** Move deliberately, stop before you click, wait a beat after a result appears. A recording with pauses is easy to cut; a rushed one is not.
- **Turn on click or key visuals** only if the tool draws them cleanly. A big yellow highlight looks like a screencast from 2011.
- **Theme:** record the theme the brand uses. Mixing light and dark screens in one demo looks like two products.

## 3. Phone recordings

- **iOS simulator, clean status bar** (the same commands `launch-graphics` uses for stills):
  ```bash
  xcrun simctl status_bar booted override --time "9:41" --dataNetwork wifi --wifiMode active --wifiBars 3 --cellularMode active --cellularBars 4 --batteryState discharging --batteryLevel 100 --operatorName ''
  xcrun simctl io booted recordVideo --codec h264 demo.mp4
  ```
  The clock follows the simulator's region: a 24-hour region draws 09:41 (`/genmedia-skills:launch-graphics` keeps the fix with its status-bar notes). On a real device, QuickTime records a connected iPhone; Control Centre records on-device (and shows a red bar in the status area).
- **Android:** `adb shell screenrecord --bit-rate 8000000 /sdcard/demo.mp4`, then `adb pull`. Demo mode gives a clean bar:
  ```bash
  adb shell settings put global sysui_demo_allowed 1
  adb shell am broadcast -a com.android.systemui.demo -e command clock -e hhmm 0930
  ```
  (check the bar on screen before trusting it; `/genmedia-skills:launch-graphics` keeps the dated status-bar notes for stills).
- Record portrait for portrait targets. Rotating a landscape recording into 9:16 costs most of the picture.
- Turn off the "recording" red pill where you can, and never deliver a frame that shows the recorder's own UI.

## 4. Performing the flow

- Rehearse once, record twice. The second take is always better.
- One flow per recording. Separate recordings for separate features are easier to cut than one long take.
- Type slowly and correctly; a typo you fix on camera costs a cut. For long text, type a few characters and let the edit speed the rest up.
- Land on the result and **stop moving** for two seconds. That still is your zoom, your poster frame and your loop's end.
- If something loads for more than two seconds, keep recording: the wait gets sped up, but the cut needs both ends of it.

## 5. Handing the recording over

Give the skill file paths, not screenshots of a player. Formats that work: `.mov`, `.mp4`, `.m4v`, `.webm` — anything the local ffmpeg reads. `source add` reports size, frame rate, duration, audio and any baked-in letterboxing, and names the targets whose aspect the recording fits.

If the recording is huge, keep it where it is: `demo-video` references the file in place and never copies it. Moving or re-exporting it later invalidates the cut (`source_changed`), so leave it alone until the video ships.
