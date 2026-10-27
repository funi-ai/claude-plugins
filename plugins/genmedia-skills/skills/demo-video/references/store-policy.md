# Store and platform rules for demo videos (verified 2026-09-20; section 1a 2026-10-07)

Read before planning a store preview and before writing anything that appears on the picture. These are facts to tell the user once, not taste to enforce.

## 1. Apple, App Review Guidelines

- **2.3.4 (previews):** "previews may only use video screen captures of the app itself. Stickers and iMessage extensions may show the user experience in the Messages app. You can add narration and video or textual overlays to help explain anything that isn't clear from the video alone."
  What follows for this skill: the picture is the recording. Narration, captions, headline overlays, an end card and a device frame around the capture are allowed; a generated or re-drawn interface is not. A "demo" assembled from stock footage of people using phones is not a preview.
- **2.3.3 (screenshots):** show the app in use, not the title art, the login page or a splash screen. The same standard is what a first frame should meet.
- **2.3.7 (metadata):** no prices, terms or descriptions that do not belong to the metadata type. Keep "$9/month" out of a preview.
- **2.3.10:** no names, icons or imagery of other mobile platforms in the metadata. An App Store preview does not show an Android device, a Play badge or an Android status bar.

## 1a. Apple, App Store creative assets (iOS 27 and iPadOS 27)

Read on Apple's creative assets specification, "Manage your App Store assets" and the asset best practices on 2026-10-07; targets `appstore-header-video` and `appstore-search-video`.

- **Not held to "in use".** Apple describes creative assets as showing the app's value, brand or excitement, apart from the in-use requirement that previews and screenshots carry. This skill still cuts only the user's real recording; a brand ground, a drawn device and short overlays around it are the room the placement adds.
- **Content.** No prices, discounts, website URLs or copyright symbols; no award or recognition the app did not receive; no Apple recognition (Editors' Choice, App of the Day, Game of the Day, Apple Design Award) even when it did; no logos of, or references to, other platforms or marketplaces; suitable for a 4+ rating whatever the app's own rating. The rows carry these as `content_rules`; nothing in `democut.py` reads the picture for them, so read the frames and the overlay text yourself.
- **Video craft Apple asks for.** A poster frame that works on its own; the value or the strongest feature first; unhurried cuts and no fast-moving visuals, which are hard to follow and less accessible; a loop with no visible jump; a picture that works silent, with sound only as brand texture (a short music loop, no sudden loud moments, looping cleanly). `time` and `validate` turn the measurable parts into warnings (`references/surfaces.md` section 1a).
- **Review.** Assets are reviewed against the app's latest version, alone through the Asset Library or with a version, and go live with it. The poster frame cannot be edited after approval.

## 2. Google Play

- The promo video is a YouTube URL, so Play's own rules are joined by YouTube's: public or unlisted, embeddable, not age-restricted, ads disabled.
- Only the first 30 s autoplays. Whatever must be seen goes there.
- Google recommends at least 80 % of the video shows the real app experience.
- Google's listing guidance discourages device imagery and people handling devices in **store graphics**; for the video, the recording itself is the safest content.

## 3. Product Hunt

- Video = a full YouTube URL. Everything else in the gallery is an image under 3 MB.
- A GIF thumbnail animates on hover only: judge it as a still first.

## 4. What must not be in the picture

- **Someone else's data.** Real names, e-mail addresses, avatars, message bodies, invoices, phone numbers, addresses, API keys, tokens, internal URLs, a signed-in account that is not the user's own demo account. Look at every frame you deliver; when something personal is there, the fix is a new recording with demo data, not a blur.
- **Another platform's marks** in an App Store preview (2.3.10).
- **Claims that are not the user's own.** Ratings, download counts, awards, "the #1 …", named competitors, press logos, customer logos: they appear only when the user supplied them and says they may be used. Never invent proof, and never let a model write it into a plate.
- **Prices in an App Store preview** (2.3.7). Prices on your own website video are fine.
- **A UI state the product cannot reach.** Speeding up a wait is honest; cutting out an error that happens every time is not; adding a screen the product does not have is a lie the store can check.

## 5. Sound and music

- Music needs a licence. Generated music through `gm.py` is fine; a track from a streaming service is not, and neither is a song "everyone uses".
- A voice that imitates a real person needs that person's permission — the same rule the other skills carry.
- A store preview plays muted first on many surfaces. Nothing may depend on the audio.

## 6. Accessibility, which is also a store fact

- Ship the cue file (`captions`). Apple and Google both show videos in contexts where sound is off, and captions are the cheapest way to keep the video usable.
- Keep the contrast of overlay text over the picture high; a lower third over a busy screen needs its own plate.
- No strobing, no rapid flashing cuts: a demo with a 3-frame flicker fails accessibility review and looks broken.

## 7. What this skill tells the user, once

When a store target is in play, the delivery says in one line: previews are screen captures of the app itself (2.3.4), the App Store cap is 15-30 s and 3 per device, Play takes a YouTube link whose first 30 s autoplay, and Product Hunt takes a YouTube link plus images under 3 MB. For a creative-asset video the line is: 5-30 s at 30 or 60 fps, it loops and plays muted (in search it cannot be unmuted), it shows on iOS 27 and iPadOS 27 or later, and the poster frame is chosen in App Store Connect and fixed once approved. That is the whole speech; it is not repeated per file.
