# Troubleshooting short video

For results that are wrong rather than failed, stages that resume oddly, lengths that do not match and costs that surprise. Failed calls and error kinds: SKILL.md Errors, then `cli-contract.md` (helper errors) and `platform.md` section 4 (platform error types). Budget everywhere: 2 re-rolls per node, something changes each time, a re-roll is a NEW job id (`clip03-r2`); editing the input of a completed id does nothing but raise `input_changed`.

## 0. Input files from the user

| Symptom | Cause | Fix |
|---|---|---|
| Read shows nothing useful, or a queued job fails with empty `fields`, `unsupported_image_format`, `image_load_error` | HEIC, AVIF, TIFF or CMYK JPEG from a phone or a designer | Convert before upload: `sips -s format png in.heic --out out.png` (macOS), `magick in.tif -colorspace sRGB out.png`, or `ffmpeg -i in.avif out.png`. Upload and register the new file under the same step name. |
| `image_too_large`, `file_too_large` | a 48 MP phone photo; clip models take start images up to 30 MB | `sips -Z 3000 in.jpg --out out.jpg` or `ffmpeg -i in.jpg -vf scale=3000:-2 out.jpg`. |
| The photo is landscape, the video is 9:16 | - | Do not crop blindly: the first keyframe is an edit that recomposes it (`production.md` production B, stage 1a). Read the result against the photo. |
| Screen recording or footage in an odd size, rate or codec | phone or screen capture | `frames.py probe`, then normalize like any clip (`finishing.md` S2). Variable frame rate: S2's `fps=` fixes it. |
| Recording longer than the clip (F10) | - | `audiokit.py extract <file> --out <span.mp3> --start <s> --duration <s>`; upload only the span. |
| Private or sensitive material | uploads become public URLs for anyone who has the link | Say so once and wait for a yes before `gm.py upload`. A real person in it: consent first (SKILL.md UX rule 4e). |

## 1. Picture

| Symptom | Likely cause | Fix |
|---|---|---|
| Every shot has a different grade or lens feel | style string paraphrased per shot; keyframes generated independently | Paste the style string byte-identical; regenerate the odd keyframes as EDITS of the anchor (`image_urls`: anchor first). Clips inherit the keyframe: fix the still, not the clip prompt. |
| Garbled letters, fake logos or UI text in a clip | the prompt asked for words, or the keyframe already contained text-like shapes | Remove every word request; add the negatives list; regenerate the keyframe with a clean reserved area; composite the text (`finishing.md` section 3). Small real UI text: shorten the shot to 2-3 s with a slow push, or cut in the user's screen recording. |
| Product label, shape or colour changed | one reference, busy prompt, big camera move | Keyframe: product reference first in `image_urls`, "unchanged in shape, label and colour", product larger in frame. Clip: smaller move (premium envelope, `craft.md`), shorter duration. Compare the last tile of the sheet with the photo. Still wrong after 2 re-rolls → hand the still to `product-photoshoot`. |
| A person's face drifts during the clip | long clip, head turn, low resolution | 5 s or less, one slow move, no turn away from camera; person references in the keyframe edit; for speech use the talking-head route (F9). |
| Morphing, extra limbs, objects appearing | too much action in one beat; vague motion words | One action per beat, in order, with seconds; add "no new objects"; lower the ordered duration; re-roll once on the same model, then try the other clip tier for that shot (say so). |
| Two camera moves, or none | two moves in the prompt; move buried at the end | One move, first sentence of the prompt, with a number. `locked-off` must be written, not implied. |
| The move runs to the last frame, no hold | hold not requested, or the duration equals the move | Order 1-2 s more than the move needs and end the prompt with "the last 1.0 s holds completely still". Or freeze in the cut: last resort, it looks like a freeze. |
| Timed ranges ignored in a multi-beat shot | models treat ranges as a request | Check the sheet tile by tile. Off by more than 0.5 s → split the shot at the beat, chain or hard-cut it. Keep ranges to three per prompt. |
| First + last frame clip warps walls or jumps | the two keyframes differ in geometry, crop or lens | Re-make the "after" as an edit of the "before" with "exactly the same camera position, lens, walls, windows"; reduce the difference; or use two static clips and the wipe (`finishing.md` S8). |
| Transition lands too early or too late (F7) | no timestamp in the prompt | State it ("at 3.0 s ... finished by 4.0 s"); order a duration where that is 40-60%. |
| Seam visible in a chain | start image was a timestamp grab, a re-encoded frame, or the style string changed | Exact last frame (`frames.py frame --at last`, PNG), same model and `resolution`, same move direction and speed, identical style string; drop the duplicated first frame of the next link. More than three links: redesign the shot. |
| Clip is not vertical, or has bars | keyframe was not 9:16; a text-to-video draft ignored the shape | Image-to-video follows the keyframe: regenerate the keyframe at 1080x1920. Never letterbox a short; crop in S2 only when the subject survives it. |
| Black or blank output | safety filter replaced the frame | Treat as a policy hit: rewrite the beat, never resend unchanged; assume it was billed (`platform.md` section 3). |
| Flicker or strobing | model artefact, neon or candle prompts, fast cuts under 0.3 s | Re-roll with "steady exposure, no flicker"; slow the cuts. Never deliver flashing content (SKILL.md, "This skill does NOT"). |
| Draft looked right, quality clip differs | different model, different motion habits | Expected: the draft proves framing, pacing and beat length, not the look. Keep prompts identical; re-roll only what the beat sheet needs. |

## 2. Voice, music, captions

| Symptom | Likely cause | Fix |
|---|---|---|
| Voice longer than the video | script over the word budget, often because hook or end-card text was moved into the voice-over; or a slow pace word ("unhurried", "calm") in `style_instructions` | Cut words (not speed, not longer clips): budget is 2.3 words per voiced second, Turkish 1.7. Regenerate the voice before any clip is ordered; cents. Re-time beats from the new word timings. The sheet's length is a hard limit. |
| The end of the voice is missing in the final, or the picture ends early | `fal-ai/ffmpeg-api/merge-audio-video` is as long as the shorter input | Give picture and voice the same length (longer end hold, a shorter script, or a trimmed picture), then mux again. Locally S4 pads and trims to `DUR` by design: check `DUR`. |
| Wrong language or accent | language field not set, or a model whose language list is a free string | Turkish: `fal-ai/gemini-3.1-flash-tts` with `"language_code": "Turkish (Turkey)"`. Any other language: read the enum in the live schema first (`routing-audio.md`). Free-string fields: one short test line before the full script. |
| Mispronounced name or number | text normalisation | Spell it the way it sounds in the TTS input only (keep the real spelling in captions); write numbers as words. |
| Clip ambience fights the voice | native audio left on | Generate clips with the audio switch off when a voice goes on top; on the draft model mute in the cut (`-an` in S2). |
| Music has vocals or a busy melody | prompt did not forbid it | `"force_instrumental": true` and "no vocals, no strong melody, leaves room for a narrator". |
| Music ends before or after the picture | `music_length_ms` set before the cut length was known | Generate music after the picture length is final (Workflow step 11); S4 trims and fades the tail anyway. Minimum length is 3000 ms. |
| Captions drift late | STT ran on a different file than the one in the cut; a lead-in was added | Transcribe the exact voice file used; pass the lead-in as `--offset`; re-run `audiokit.py captions` on the saved `.result.json` (free). |
| Captions misspell names or Turkish words | speech-to-text guessed | Fix the `.srt` by hand against the script, or run forced alignment with the exact text (`finishing.md` C1). With `auto-subtitle` the model transcribes again by itself: prefer `veed/subtitles` with `srt_content` when spelling matters. |
| Burned captions sit under the platform interface | bottom-anchored style | Move them into the safe box (`platforms.md` section 2): `position` plus `y_offset`, or `customization.position`; check one extracted frame. |
| Burned captions look soft | a re-encode or the upscale ran after the burn | Burn last. Redo from the un-captioned mix. |
| Talking head job fails, `fields` empty | audio at or over the model's limit, or a portrait without a clear frontal face | Probe the chunk (`audiokit.py probe`); smaller `--max-chars`; `"resolution": "720p"` allows under 60 s, the default `1080p` under 30 s. Face errors need another portrait. |
| Visible jump between talking-head chunks | no cutaway over the join | `finishing.md` S7: 2-3 s of b-roll starting about 1 s before the join. |

## 3. Stages, state, resume

| Symptom | Cause | Fix |
|---|---|---|
| `status: "pending"` again and again | long queue (new accounts render 2 jobs at a time) | Rerun the same batch command, Bash timeout 600000 ms. Six reruns without any state change → report, offer to continue later; never resubmit. |
| A rerun paid for jobs again | the command ran from another directory, or the label changed | The ledger is `.genmedia/runs.jsonl` in the current directory and resume is by label + id. Always run from the project root with the one project label. |
| `fill` reports `unresolved` | upstream job not completed, a user file never registered, or a typo in the id | `pipeline.py urls --label <slug>` shows what exists. Finish or register it; never paste a guessed URL. |
| `input_changed: true` | a completed id's prompt was edited | Restore the plan text, or re-roll under a new id and point later stages at it. |
| `--retry-failed` resubmitted more than intended | it redoes every failed id in that plan file | Put only the repaired ids into a small plan file (same label, same ids) and run that. |
| Old CDN URL fails with a download error | fal URLs expire | Re-upload the local file (`gm.py upload`), register it again with `pipeline.py add ... --url`, `fill` again. |
| The manifest lists problems | unfinished or failed ids, files missing, a bare-string result never fetched | Resolve each: re-roll or drop the node from the cut and say so; `pipeline.py fetch` for compose results. Deliver only with an empty `problems` list or an explanation per item. |
| The user changed the beat sheet after clips exist | approval covered the old version | New beat sheet version, new approval. Reuse every node whose beat did not change; re-roll only changed beats under new ids; re-price the delta before spending. |
| The session ended mid-project | - | SKILL.md Step 0: read `plan.md`, run `pipeline.py urls`, continue at the first unfinished step. |

## 4. Cost

| Surprise | Why | Do |
|---|---|---|
| A 2 s beat cost as much as a 4 s one | the quality clip model's minimum is 4 s; ordered seconds are billed | Short beats go to the value model (minimum 2 s), or merge two short beats into one shot. |
| Value-tier clips cost double the estimate | that model's `resolution` defaults to `1080p` | Always send `"resolution": "720p"`. |
| Draft clips cost double since 2026-09-30 | the launch discount ended | Re-price with `gm.py price --explain`; the draft pass is still cents. |
| The estimate was far below the ledger sum | re-rolls, the draft pass or the finish were not in the plan | The plan total includes every stage: drafts, upscale, captions, overlays. Report spend with `gm.py ledger --label <slug> --sum` at every checkpoint. |
| `duration: "auto"` slipped through | default on the quality model | Lint item 10. A job already submitted that way: wait for it, probe its length, record the real cost basis. |
| Upscale costs more than the clips (value tier) | per-megapixel pricing scales with frames | Use the free scale for value and draft tiers (`finishing.md` section 5); keep the cut at 24 fps. |
