# Troubleshooting a product shoot

Symptom → cause → fix, for problems that are specific to product work. Output defects on the product itself (label, shape, colour, count, hands) are in `fidelity-qa.md` section 3. Platform error types: `platform.md` section 4. Helper and ledger behaviour: `cli-contract.md`. `gm.py` and `pipeline.py` abbreviate the calls shown in SKILL.md.

## 1. Input photos

| Symptom | Cause | Fix |
|---|---|---|
| Queued job fails with empty `fields`, or `unsupported_image_format` / `image_load_error` | HEIC, AVIF, TIFF or CMYK JPEG straight from a phone or a designer | Convert to PNG or sRGB JPEG before upload: `sips -s format png in.heic --out out.png` (macOS), or `magick in.tif -colorspace sRGB out.png`, or `ffmpeg -i in.avif out.png`. Upload the new file and register it again under the same step name |
| `image_too_large`, `file_too_large` | 48 MP phone photo | `sips -Z 3000 in.jpg --out out.jpg`, `magick in.jpg -resize 3000x3000 out.jpg` or `ffmpeg -i in.jpg -vf scale=3000:-2 out.jpg`. Bria product-shot: at most 12 MB |
| Photo arrives sideways | EXIF orientation not baked in | `magick in.jpg -auto-orient out.jpg`, or re-save from a viewer; then Read it again to confirm |
| Several products or clutter in the photo | model cannot tell which item is "the product" | Crop to the product before upload. For packshots Pixelcut isolates the main subject; check that it picked the right one |
| Source is small or blurry (label unreadable to you) | the model cannot preserve what is not there | Ask for a closer, sharper photo: daylight by a window, plain wall, phone at label height, no flash. Do not upscale a label to "recover" text |
| Only one angle supplied, the plan needs others | unseen sides get invented | Keep the camera within the covered arc, or ask for the missing side. Never show the back of a pack you have not seen |
| White or transparent product on a white background | cut-out loses edges; glass disappears | Packshot on light grey (`color` 240,240,240) or ask for a photo on a mid-tone backdrop. Glass, liquids and chrome: prefer `fal-ai/bria/background/replace` or the generative route with a "clear glass, visible rim highlights" line, and check edges closely |
| Holographic, foil, metallic or embossed details | generative models flatten or repaint them | Non-generative routes wherever possible; on scenes, name the finish in the lock ("brushed gold foil, not yellow ink") and accept a lower pass rate: plan one re-roll into the estimate |
| Tiny legal text, barcode, ingredients panel | no model reproduces 6 pt type | Keep that face away from the camera or small enough to be unreadable. Never deliver legible fake ingredients or barcodes |
| The user sends a render or mock-up instead of a photo | fine as a reference; the result inherits its look | Proceed, and say the output is only as accurate as the mock-up |
| The photo shows a real person (model wearing the item) | likeness | Ask for consent once; or crop to the product |

## 2. Look and approval

| Symptom | Fix |
|---|---|
| Both hero candidates rejected for the look | Do not reword; change a category pick in `variation-matrix.md` (surface family, light, framing) and show two new candidates. After two rejected rounds, ask one question with 3 labelled look options; this is inside the question budget only if budget is left, otherwise offer it as part of the checkpoint message |
| Both hero candidates fail the same fidelity check | The route is wrong, not the seed: label → GPT Image 2.5; shape → frontal angle; then re-run the hero. It is still the hero stage: no variants yet |
| User wants a different look after stage 2 ran | New plan version (v2), new hero, new approval. Offer to keep the approved v1 shots as a separate set |
| User approves the hero "but make it a bit warmer" | That is a change, not an approval: adjust the look string, re-run the hero (one candidate is enough), confirm |
| Variants look like a different campaign | Hero missing from `image_urls`, or look string paraphrased. Restore both; see F9 in `fidelity-qa.md` |
| Every shoot in the session looks alike | You reused the previous look. Apply the two-of-three difference rule in `variation-matrix.md` section 4 |
| The user asks for a banned cliché by name (podium, splash, petals) | It is their brand: do it, once, well. The ban list guards your defaults, not their wishes |

## 3. Plans, references and resuming

| Symptom | Cause | Fix |
|---|---|---|
| `input.image_urls: '@product' is not a URL` (exit 2, nothing sent) | the `.tmpl.json` was run instead of the filled plan | `pipeline.py fill`, then run the `--out` file |
| `fill` reports `unresolved` for `@product` | the file was uploaded but never registered, or registered under another label | `pipeline.py add --label <slug> --step product --path <file> --url <cdn_url>`; check with `pipeline.py urls --label <slug>` |
| `fill` reports `unresolved` for `@hero[1]` | the hero ran with `num_images: 1`, or candidate 2 failed to download | Use `@hero` or `@hero[0]`; or re-run the missing output as a new id |
| Job with a filled hero URL fails with `file_download_error` days later | the CDN URL expired | Upload the local hero file again and register it as a new step (`hero-ref`); point the remaining templates at `"@hero-ref"` |
| Try-on or Pixelcut composite billed but returned nonsense | an unfilled `@reference` in `model_image`, `garment_image` or `background.image_url` slipped through (no URL check on those fields) | Always run the filled plan; search the filled file for `"@` before running |
| Batch says `pending` | normal for a slow queue | Run the same command again with a 600000 ms timeout. Never resubmit; stop after 6 reruns without change and report |
| `input_changed: true` on a completed id | you edited a finished job's prompt hoping for a re-roll | A re-roll is a new id (`s03-r2`) |
| `manifest` lists a failed id you dropped on purpose | failed ids stay failed | Log the drop in `plan.md`, say it in the delivery. Or repair it with `--retry-failed` |
| The session ended mid-shoot | | Step 0 resume: `plan.md` has the lock, look, hero pick and log; `pipeline.py urls --label <slug>` has every output |

## 4. Try-on and people

| Symptom | Fix |
|---|---|
| Garment rendered as the wrong category (shirt as a dress) | Set `category` explicitly (`tops`, `bottoms`, `one-pieces`) instead of `auto` |
| Flat-lay garment looks pasted on | `garment_photo_type: "flat-lay"`; garment photographed unfolded on a plain background |
| Print, logo or buttons changed | Try-on models redraw the garment: QA it like a label (F1 to F4). Re-roll with `mode: "quality"` and `num_samples` 2 to 4; second opinion on `google/virtual-try-on`; several pieces or accessories on `bria/fibo-edit-1.5/virtual-try-on` |
| Long dress, coat or layered outfit fails | Full-body model photo with the whole garment area visible; one garment per call |
| Swimwear or underwear blocked | The default `moderation_level` is `permissive`, which blocks only explicit content; `conservative` blocks these categories. Do not try `none`. A block at the default is final: tell the user |
| Result too small for the channel | Read the returned width and height; upscale the approved result with `fal-ai/seedvr/upscale/image` |
| Person's face changed | Try-on is not an identity tool. For a recurring model use `/genmedia-skills:character`, then try-on onto that model's approved image |
| The user wants "a model like <celebrity>" | No real-person likeness without consent. Describe age range, styling and mood instead |

## 5. Safety filters and false positives

Product prompts trip filters for innocent reasons: skincare on bare skin, lingerie and swimwear, "shot", "nude" as a colour name, "intimate", "sensual", "bare", medical and supplement wording, children's products with a child in frame.

- A `content_policy` result, or a black image, is never resent unchanged and the checker is never disabled.
- Rewrite plainly: colour names as "beige" or "sand", "close-up of a forearm" instead of "bare skin", "product photo" instead of "shot"; remove mood words that carry a second meaning; remove the person if the product does not need one.
- One changed retry on the same endpoint. A second block on clearly benign content → one attempt on the other family (Seedream ↔ GPT Image 2.5), and tell the user.
- Assume blocked jobs were billed; count them in the spend line.

## 6. Cost surprises

| Surprise | Cause | Prevention |
|---|---|---|
| Seedream shots cost double | `image_size` omitted (`auto_2K`) or an area above 1536x1536 | Sizes from the table in `modes.md` only |
| GPT Image shot cost four times the estimate | `quality` left at a higher tier than planned, or `num_images` above 1 | Set `quality` and `num_images` in every job |
| Ten images from one Bria call | `placement_type: "automatic"` | `manual_placement` with one `manual_placement_selection` |
| The total is far above the card | re-rolls, plus blocked or failed-after-start jobs | Report spend with `gm.py ledger --label <slug> --sum`; the card already said re-rolls are extra and they need no new approval inside the budget of 2. Added shots, a dearer model or a new paid step (upscale, outpaint, extra ratios) are a plan change: re-price, show the new total, apply the cost gate again |
| A price in this skill differs from `gm.py price` | dated hint | The live price wins. Quote the higher when two live sources disagree |

## 7. Marketplace and ad-platform rejections

This skill knows only the commonly cited basics; every platform publishes and changes its own rules. When an image is rejected, ask the user for the rejection text and fix that, do not guess.

| Reason given | Usual fix |
|---|---|
| Background not pure white | Packshot via `pixelcut/product-photo` with `color` 255,255,255 and no backdrop image; JPEG compression can grey the corners: deliver PNG or high-quality JPEG |
| Product too small in frame | Lower `margin.all` |
| Text, badge, watermark, border or props in the main image | Main image = mode 1 only. Lifestyle and ad shots go to secondary slots |
| Image too small for zoom, or wrong ratio | Re-run the packshot at a larger `image_size` from a sharper source; ratios from `modes.md` |
| "Misleading" or "does not match the product" | A generated rendition drifted from the real item, or props imply things that are not included. Return to non-generative routes for that slot |
| Ad rejected for claims or before/after imagery | Copy and claims are the user's responsibility; this skill adds none. Remove the claim; do not rephrase it to slip through |

## 8. Legal and honesty lines

- Only the user's own brand on the product. No competitor products in frame, no partner, retailer, certification or award marks unless the user confirms the right to use them and supplies the artwork.
- No invented reviews, star ratings, "bestseller", "dermatologist tested", "organic", "-50%" or prices. If the user supplies true wording, it is set as text later, not painted by the scene model.
- "What's in the box" shows only what is in the box. Scale shots use the real dimensions.
- A generated person is a synthetic model: say so if the user asks, and recommend disclosure where the platform requires it (check the platform's current rules).
- Check the model page's `Commercial use` badge before client work (`platform.md` section 9).
