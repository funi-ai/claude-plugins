# Localization

How one deck carries several languages without looking translated: what to rewrite, how line arrays differ per locale, what each script does to the layout, how localized captures and their fallback work, and the read-back every locale gets before delivery. Platform facts (store locale codes, what Play does when a localized image is missing): **Verified: 2026-09-20** against the pages named in section 9; the official page wins when it disagrees. Length figures are rules of thumb, not measurements. `launchkit.py` abbreviates the call shown in SKILL.md.

## 1. Transcreation, not translation

1. The unit of localization is the **approved idea of a slide** (its angle and the screen that proves it), not the English sentence. Write each locale's headline from the idea, in the words a native speaker would use in that situation.
2. Idioms, puns and rhythm do not travel. "Before payday" becomes whatever that market calls the day money arrives; if nothing fits, change the angle for that locale and keep the capture.
3. Proof travels only when it is true there. A rating, an award or a press quote from one market is not copied into another locale's `badge` unless the user says it applies.
4. Product names, feature names the interface shows, and the user's brand words stay as the app spells them in that locale's capture.
5. You write the first version; the user or a native reader approves it. Say plainly when you are not a reliable writer of a language, and never deliver a locale nobody has read.
6. Every locale passes the same gates as the default one: `launchkit.py text` checks budgets, numbers and claims per locale.

## 2. Deck mechanics

- `locales` lists every locale of the deck, `default_locale` names the one the copy was approved in, `rtl_locales` names the right-to-left ones (`ar`, `he`, `fa` and `ur` render right-to-left even when the list leaves them out; `init` fills it in for them).
- Every slide carries a `copy` entry per locale. **Line arrays may differ in count and in break position**: two lines in English, three in German, one in Japanese is normal. Breaks are authored per locale; nothing is re-wrapped.
- `emphasis` must occur in that locale's headline exactly as written. It is rarely the translated English word: pick the payoff word of the new sentence.
- A locale listed in `locales` but missing on a slide → error `copy_missing`. A locale key in a slide's `copy` that `locales` does not list → error `copy_unused`. Both are fixed in the deck, not by deleting the check: add the lines, or remove the stray key.
- Too long → `copy_too_long` for that locale's page only (the other locales of the slide still render). The answer is a rewrite in that language. Never shrink one locale's type below the floor, and never solve it by dropping a locale's diacritics or abbreviating words the interface spells out.

## 3. Expansion and contraction

| Family | Against an English line | What to do |
|---|---|---|
| German, Dutch, Finnish, Hungarian | clearly longer; single words can exceed a whole line | verbs instead of compounds, three lines instead of two, drop the `sub` first |
| Turkish | similar word count, longer words through suffixes | budget by characters; choose the shorter construction (section 4) |
| French, Spanish, Italian, Portuguese | somewhat longer; articles and prepositions add short words | cut the article where headline style allows; watch orphaned two-letter words at line ends |
| Russian, Ukrainian, Polish, Czech | longer words, no articles | three lines; check the heavy weight still separates the letters at small size |
| Chinese, Japanese, Korean | far fewer characters, each one wider | fewer characters per line and a smaller base size (section 6) |
| Arabic, Hebrew | similar or shorter; joined letters and marks need vertical room | slightly looser line spacing; right-to-left rules (section 7) |

The order of remedies is always the same: a shorter native wording → another line break → one more line → drop the `sub` → a different angle for this locale. Smaller type is not on the list: the fit pass already uses the room it has.

## 4. Turkish

| Risk | What goes wrong | What to do |
|---|---|---|
| Dotted and dotless i | a generic upper-casing routine turns `iyi` into `IYI`; Turkish needs `İYİ`. The pairs are i → İ and ı → I | never upper-case by hand or in CSS; take the `upper` string `launchkit.py text --full` prints next to every line, which follows the locale for `tr` and `az` (`"ilk kitabı"` → `"İLK KİTABI"`) |
| The reverse | lower-casing `IŞIK` must give `ışık`, not `işik` | copy the user's own casing; do not re-case their brand or feature names |
| Suffix-heavy words | `kişiselleştirilebilir`, `bildirimlerinizden` do not fit a 16-character line | rewrite with a verb and a pronoun: `["Sana göre", "ayarla"]`; never hyphenate a headline word |
| Orphaned particles | `de`, `da`, `ki`, `mi`, `mı`, `mu`, `mü` alone at the start of a line read as a mistake | the particle stays on the line of the word it follows |
| Orphaned postpositions | `için`, `ile`, `gibi`, `kadar` alone on the last line | keep them with their noun: `["Ailen için", "tek liste"]`, not `["Ailen", "için tek liste"]` |
| Apostrophe suffixes | `Mola'yı`, `iPhone'unda` broken after the apostrophe | name, apostrophe and suffix are one unbreakable word |
| Percent and decimals | `%50`, `4,8`, `1.250,00` | the percent sign comes first, the decimal separator is a comma; follow the capture (section 8) |
| Formal or informal | `siz` and `sen` mixed across slides | one register per deck, taken from the app's own interface |

Every one of ı İ ş Ş ğ Ğ ü Ü ö Ö ç Ç renders correctly as HTML text; what fails is a font file without those glyphs. A custom face in `theme.font.files` is checked in the read-back of section 10 before the set is composed in full.

## 5. German and other compounding languages

- A compound is one word and one line: `Ausgabenübersicht` has 17 characters and no legal break. Rewrite around a verb (`["Sieh, wohin", "dein Geld geht"]`) rather than hyphenating.
- Nouns keep their capitals; do not force sentence case rules from English onto them.
- Avoid all caps: `ß` turns into `SS` or the rare capital `ẞ`, and either looks odd in a headline.
- `du` or `Sie`: take the register from the German capture. Mixed registers across slides are a Retake of the copy.
- Dutch, Swedish, Norwegian, Danish and Finnish compounds follow the same rule: one word, one line, or a rewrite.

## 6. Chinese, Japanese, Korean

1. **Smaller base size, fewer characters.** A full-width character is about as wide as it is tall, close to twice a Latin letter in a heavy sans. Where a Latin line holds 16 characters, plan 8 to 10. For `ja`, `zh` and `ko` the script starts a layout at 90 percent of its Latin size and drops the negative letter-spacing (as it does for right-to-left locales, `th` and `hi`), so that a natural phrase fits on one line.
2. **No spaces does not mean break anywhere.** Break between phrases. Never split a word or a compound, never begin a line with closing punctuation, a small kana or a particle that belongs to the previous word, and never leave one character alone on the last line.
3. Japanese mixes scripts; Korean breaks between words (it has spaces); Simplified and Traditional Chinese are two locales with two texts, not one text in two fonts.
4. **Fonts.** The `system` stack names no CJK face; the browser falls back to whatever the machine has. Empty boxes or a serif fallback in the PNG mean the face is missing: ask for a font file for `theme.font.files`. Heavy CJK weights fill in at small sizes: check the 220 px view of the `sheet`.
5. A native reader confirms wording and breaks before delivery. Say so in the plan card when the user adds a CJK locale.

## 7. Right-to-left locales

List them in `rtl_locales` (`ar`, `he`, `fa`, `ur` are recognised by their language code as well). The page then sets `dir="rtl"` on text blocks and mirrors the text alignment inside each block.

| Mirrors | Does not mirror |
|---|---|
| direction and alignment of headline, `sub` and `badge` text | the device position, the text block's place and the rest of the layout geometry |
| the reading order of mixed lines, handled by the browser | the capture: a real right-to-left interface comes from `by_locale`, never from flipping the image |
| | the lockup (logo, or icon and name), `decor` placement, plates |
| | digits and Latin brand names inside the sentence, which stay left-to-right |

- An Arabic headline over a left-to-right interface tells the visitor the app is not localized. Ask for the localized capture; without it, say so in the delivery.
- Mixed strings (a Latin product name, a version number, a percentage) are where punctuation jumps to the wrong end of a line. Read them back from the PNG, character by character.
- Arabic has no capital letters and `emphasis` should cover whole words: a colour change inside a joined word can break the joining in some faces.
- Mirroring a plate or a hand-held scene is a new plate, not a CSS flip: the screen quad and the light direction belong to the file.

## 8. Numbers, currency and dates

1. **Captures are never edited.** Amounts, dates, separators and currency symbols inside a capture are the app's own output for that locale. A `tr` slide showing `$1,250.00` needs a `tr` capture, not a retouch.
2. **Copy follows the capture.** Write numbers in the headline the way the interface under it writes them: separator, currency position, 12 or 24 hour clock.
3. The numbers gate compares what is written. A value that appears as `4.8` in English copy and `4,8` in Turkish copy needs both spellings in `facts.numbers`, and both must be the same fact.
4. Prices differ per market and go stale; they stay off store targets anyway (`store-policy.md` section 6).
5. Dates: prefer none. A slide that says "2026" is outdated in January.
6. The status bar times (9:41 on iOS, 9:30 on Android) are fixed by this skill and are not localized.

## 9. Localized captures and store locale codes

`captures.<id>.by_locale` maps a locale to its own file; `capture add --locale <l>` archives it under `captures/<l>/` and records it (the default file must exist first). A locale without an entry **falls back to the default capture**. That is allowed, the script does not flag it, and so you always report it: the delivery note lists, per locale, which slides show the default-language interface ("tr: slides 2 and 4 use the English capture"). Play itself shows the default language's graphics when a locale has translated text but no images of its own, so a half-localized set is a step up, but the user should know which half they have.

Deck locale keys are the author's short names (`en`, `tr`); the output folder uses the same key. The stores use their own codes, and they differ from each other:

| Language | App Store Connect | Google Play |
|---|---|---|
| English (U.S.) / (U.K.) | `en-US` / `en-GB` | `en-US` / `en-GB` |
| Turkish | `tr` | `tr-TR` |
| German | `de-DE` | `de-DE` |
| French / French (Canada) | `fr-FR` / `fr-CA` | `fr-FR` / `fr-CA` |
| Spanish (Spain) / Latin America | `es-ES` / `es-MX` (Mexico) | `es-ES` / `es-419`, also `es-US` |
| Portuguese (Brazil) / (Portugal) | `pt-BR` / `pt-PT` | `pt-BR` / `pt-PT` |
| Italian, Japanese, Korean, Russian | `it`, `ja`, `ko`, `ru` | `it-IT`, `ja-JP`, `ko-KR`, `ru-RU` |
| Chinese (Simplified) / (Traditional) | `zh-Hans` / `zh-Hant` | `zh-CN` / `zh-TW`, also `zh-HK` |
| Arabic | `ar-SA` | `ar` |
| Hebrew | `he` | `iw-IL` |
| Dutch, Polish, Swedish, Norwegian | `nl-NL`, `pl`, `sv`, `no` | `nl-NL`, `pl-PL`, `sv-SE`, `no-NO` |

App Store Connect lists 50 languages and locales; Play's translation page lists more than 80 codes. Give the user the store code next to each locale folder in the delivery note; do not rename their folders unasked.

Sources, opened 2026-09-20: https://developer.apple.com/help/app-store-connect/reference/app-information/app-store-localizations (languages) · https://developer.apple.com/documentation/appstoreconnectapi/managing-metadata-in-your-app-by-using-locale-shortcodes (codes) · https://support.google.com/googleplay/android-developer/answer/9844778 (Play codes, default-language graphics).

## 10. QA per locale

Run it for every locale, on the rendered PNG, not on the deck.

1. `launchkit.py text` is clean for the locale: no `copy_missing`, no `copy_unused`, and no entry for it in `findings[]` (budgets, numbers, claims).
2. Compose **slide 1 of the locale first**. Read its headline back from the PNG letter by letter, and write down what you see before comparing it with the deck. Every diacritic present, no empty boxes, no fallback face in the middle of a word.
3. Then the full locale. For each slide: every authored line sits on one row; no word is split; no particle, postposition or single character is orphaned; `emphasis` colours the intended word and nothing else.
4. `fit_scale` per slide (`warnings_by_kind.fit_scale` in the `compose` answer lists the pages, the values are in the details file): a locale that sits below 0.9 on most slides needs shorter copy, not a smaller system.
5. Right-to-left: alignment mirrored, device not mirrored, mixed Latin and digits in the right order, punctuation at the correct end.
6. Capture language matches the headline language, or the mismatch is on the fallback list of section 9.
7. Upper-cased words came from the `upper` field of `launchkit.py text --full`. Check İ and I by eye once more.
8. The small view of the `sheet` for this locale: the longest language is where the small-size test fails first.
9. Name in the delivery who should read the locale before upload when you are not a native-level writer of it.
