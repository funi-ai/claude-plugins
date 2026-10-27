# Marketplaces: labelled basics, sizes, card order

Everything on this page is a **commonly cited basic, not a rule book**. Marketplaces change their image rules, apply them per category and enforce them unevenly. Say so in the delivery, in these words or their translation: "check <marketplace>'s current image rules for your category before uploading". Never tell a user that an image "complies" or "will be accepted". Sizes below are safe defaults the user can override, never requirements.

## 1. What holds almost everywhere

- **The first image is the product, alone, on a plain light background** (pure white on Amazon-style marketplaces), whole in frame and filling most of it, with no added text, badges, borders, watermarks or props. That is why card 1 is a non-generative packshot (`pixelcut/product-photo`).
- **Later images may explain:** infographics, dimensions, in-use scenes, kit contents. How much text they tolerate differs by marketplace and category (section 2).
- **What gets images rejected or listings suppressed:** promotional wording (prices, discounts, "free shipping", "best seller"), ratings and review quotes, contact details and web addresses, claims the seller cannot document (medical, "certified", "No. 1"), other brands' logos, comparisons against named competitors, misleading accessories that are not in the box. This skill refuses these regardless of marketplace.
- **Square is the safe ratio** unless the marketplace is known for another one. Longest side of 1600 px or more keeps zoom working where zoom exists; 2000x2000 is the everyday seller default and this skill's default.
- **sRGB JPEG** is accepted everywhere; PNG almost everywhere. Deliver the main image as JPEG and the cards as PNG masters, plus JPEG copies when the marketplace or a file-size limit asks for them (`cardkit.py fit --out <file>.jpg`, `--max-kb` when a limit is known).
- **Phones first.** Most shoppers see the card about 400 px wide. The text budget and the 3 percent label height in `set-system.md` exist for that.

## 2. Per marketplace (commonly cited; check the current rules)

| Marketplace | Main image | Other images | Ratio and size default here | Notes |
|---|---|---|---|---|
| Amazon | pure white background (RGB 255), product fills roughly 85 percent of the frame, no text, logos, watermarks or props | infographics, lifestyle and dimension images are common in the additional slots | 1:1, 2000x2000 (1000 px on the longest side is the commonly cited minimum for zoom) | Category style guides add their own rules (apparel, jewellery, food). Enhanced "A+" content uses fixed module sizes: section 3. |
| Trendyol | product on a plain light background, no text, logo or watermark | moderated per category; text-heavy or promotional images are commonly rejected in several categories | portrait 2:3, 1200x1800 is the widely used seller size | The intake message carries one line asking whether the category accepts images with text. "No" → the text-light set of section 4. No answer → the full set, with "text cards may be refused in some Trendyol categories" in the plan card's Assumptions. Never a second question round. |
| Hepsiburada | product on white, no text or watermark | moderated per category, similar caution as Trendyol | 1:1, 2000x2000 | The seller panel's image guide for the category decides; this skill states no pixel limits for it. |
| Etsy | no white-background rule; the first photo is cropped to a thumbnail, so keep the product centred with room around it | infographic and size images are common | landscape 4:3, 2048x1536 (Etsy's long-standing advice: about 2000 px on the shortest side) | A lifestyle or styled first photo is normal here: the in-use card can lead. Handmade and vintage claims are the seller's responsibility. |
| Shopify or own store | the theme decides; consistency across products matters more than any rule | anything | 1:1, 2048x2048 or 2000x2000; one ratio for the whole store | No marketplace moderation, so the honesty rules of this skill are the only guard. Large files slow the page: offer JPEG copies. |
| Other (n11, Çiçeksepeti, eBay, Walmart, Allegro, ...) | assume the Amazon-style main image | assume the cautious reading: little text | 1:1, 2000x2000 | Say that you applied generic defaults and that the seller panel decides. |

Marketplace not named → generic defaults: square 2000x2000, white main image, cards in the order of section 4, and one line in the plan card's Assumptions.

## 3. Master sizes: what to render, what to deliver

GPT Image 2.5 accepts only sizes whose two sides are multiples of 16, between 655,360 and 8,294,400 pixels, aspect at most 3:1, longest side at most 3840. Seedream 5.0 Pro bills its base price up to a 1536x1536 area. Pixelcut takes any size; `bria/product-dimensions` renders squares only (`output_size` up to 2200). Render the **master** of the right ratio, then scale with `cardkit.py fit` (pure scaling, never a crop).

| Target | Ratio | GPT Image master | Seedream master (text-free) | Pixelcut main | Deliver |
|---|---|---|---|---|---|
| Square listing (default) | 1:1 | 2000x2000 | 1536x1536 | 2000x2000 | as rendered |
| Square, budget | 1:1 | 1600x1600 | 1536x1536 | 1600x1600 | as rendered |
| Portrait 2:3 listing (1200x1800) | 2:3 | 1344x2016 | 1248x1872 | 1200x1800 | `fit --size 1200x1800` |
| Landscape 4:3 listing | 4:3 | 2048x1536 | 1760x1320 | 2048x1536 | as rendered |
| Amazon A+ standard header module, 970x600 | 97:60 | 1552x960 | - | - | `fit --size 970x600` |
| Amazon Premium A+ full-width module, 1464x600 | 61:25 | 1952x800 | - | - | `fit --size 1464x600` |
| Store or brand-page banner | 16:9 | 2560x1440 | - | - | as rendered, or `fit --size 1920x1080` |

- The A+ module sizes are the commonly cited ones; modules and their sizes change, so confirm the module's size in the A+ editor first. Another size → compute its master: reduce the ratio to lowest terms a:b, then render a x k by b x k with the smallest k that makes both sides multiples of 16 and the pixel count at least 655,360 (970x600 → 97:60 → k = 16 → 1552x960; 1464x600 → 61:25 → k = 32 → 1952x800). A ratio wider than 3:1 cannot be rendered in one piece: say so and offer the 3:1 master with the user cropping in the module editor.
- The Seedream master is smaller than the other cards of a 2000 px set and below the 1600 px zoom guidance of section 1. Say so in the plan card's Assumptions. The user wants every card at the set size → render the scene on GPT Image 2.5 Sunburst edit at the set master instead (priced like a text card), or on Seedream at up to 2048x2048 in its higher price tier (`gm.py price ... --explain`); never upscale it with `fit` without saying that edges soften.
- The Bria dimensions card is square. In a 2:3 or 4:3 set, take route B of `card-types.md` for that card, or deliver the square card as it is when the marketplace accepts mixed ratios (say which you chose).
- `fit` refuses a ratio mismatch above 1 percent (`kind: "ratio_mismatch"`). That is deliberate: cropping a card cuts text. Render the right master instead.
- No ffmpeg and no `sips` → `kind: "tool_missing"`: deliver the masters, state their pixel sizes from `cardkit.py probe`, and say that the marketplace uploader or any image editor can scale them because the ratio is already exact.
- Upscaling a card for print or a larger slot is outside this skill; render a larger master instead (GPT Image goes up to 3840 on the longest side, priced from the 3840x2160 row).

## 4. Default sets and order

The listing order below is what `cardkit.py facts` returns in `cards.possible`; keep it unless the user or the marketplace suggests otherwise.

| Slot | Card | Why here |
|---|---|---|
| 1 | `main` | search result and first impression; the marketplace rules bite hardest here |
| 2 | `benefits` | the shopper who clicked wants the reasons next |
| 3 | `inuse` | size and context, the most common unanswered question |
| 4 | `dimensions` | hard numbers right after the impression of size |
| 5 | `materials` | what it is made of, or what is inside |
| 6 | `howto` | removes doubt about use or setup |
| 7 | `inbox` | what arrives |
| 8 | `range` or `trust` | only with user-supplied facts; drop before crowding the set |

- Typical set: 6 to 8 cards. Most marketplaces show a limited number of image slots (often fewer on phones): check the slot count for the category and put the strongest cards first.
- Text-cautious marketplace or category → `main`, `inuse` (no caption), `dimensions`, `inbox`, one `benefits` card with three short labels; move the rest of the copy to the listing text.
- Etsy or a lifestyle-led store → `inuse` may take slot 1 when the user agrees; the white packshot moves to slot 2.
- Banners (`banner`) are delivered in their own folder, not in the listing order: a second `cardkit.py order --out-dir genmedia-output/<slug>/banners --item ...` call.

## 5. When a marketplace rejects an image

Ask the user for the rejection message, word for word. Map it, fix only that:

| Message is about | Likely cause | Fix |
|---|---|---|
| background, "not pure white", shadow | drop shadow or off-white edge on the main image | rerun `c01-main` under a new id without `shadow`; check the corners are 255,255,255 by eye at full zoom |
| text, logo, watermark on image | an infographic in a slot or category that wants clean photos | move that card later or drop it; offer the text-free variant of the card |
| promotional or misleading content | a claim word, a badge-like shape, an accessory not in the box | remove it; re-check `cardkit.py text` warnings; never argue the claim |
| size, resolution, ratio, file size | wrong master or an oversized PNG | `cardkit.py fit` to the stated size, JPEG, `--max-kb` with the stated limit |
| product does not match, wrong variant | the card shows a colour or kit the listing does not sell | the facts or the photo were for another variant: confirm with the user, re-render that card |

Do not promise that the fix will be accepted; say what changed and that the marketplace decides.
