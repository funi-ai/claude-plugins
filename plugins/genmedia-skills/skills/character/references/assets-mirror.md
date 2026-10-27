# fal Assets mirror (optional)

fal Assets has a "character" entity: a named bundle of 1 to 20 reference images with a description and an `@identifier`. fal's web apps (Sandbox, fal Agent) expand that `@identifier` in prompts. The `genmedia` CLI does not: `genmedia run` sends `@mara` as literal text. A mirror therefore adds exactly two things: the character shows up in fal's web apps, and generations can be filed under it in the Assets library. It adds nothing to fidelity, it is not a trained identity, and it does not extend the lifetime of any file.

The local sheet stays the source of truth. The mirror is rebuilt from it, never the other way round (except the one-time import in section 5).

Status of this file: command syntax checked against `genmedia assets ... --help` (v0.7.0) and fal's Platform API description on 2026-09-19. fal Assets was not enabled on the account used for verification, so response handling below tells you to read what comes back instead of assuming it.

## 1. When to mirror

All three must hold; otherwise skip silently and never mention Assets:

1. The user asked for it ("make it available in fal", "I want to @mention it in the fal sandbox", "sync my characters").
2. `gm.py preflight` reports `assets.enabled: true`.
3. The character has at least one reference. For a real person, consent is already recorded in the sheet.

`assets.enabled` is `false` or `"unknown"`, or any Assets call fails with this shape (stderr, exit 1):

```json
{"error": "Assets GET /characters failed (403)",
 "details": {"error": {"type": "authorization_error",
   "message": "fal Assets is not enabled for this account. Visit https://fal.ai/assets to enable fal Assets before using the Platform API."}}}
```

Then stay local. Only if the user explicitly asked for the mirror, tell them once that fal Assets is switched off for their account and that they can enable it themselves at https://fal.ai/assets; do not retry until they say it is done.

Creating, updating and uploading change the user's fal account. They are not pre-approved in this skill; expect a permission prompt and do not work around it.

## 2. Limits

| Field | Limit |
|---|---|
| Name | 255 characters |
| Description | required, 2000 characters. Use the anchor; `character.py init` warns when it is longer. |
| Identifier | 64 characters, optional, unique per account, **cannot be changed later**. Use the handle. |
| Reference images | 1 to 20 per character. Each is a `request_id` or `vector_id` of media already in fal, or a URL for external images. |
| Lookup | There is no get-by-identifier. List and filter on `character_identifier`. |

## 3. Create the mirror

1. Already there? List and look for the handle in `character_identifier`:

```bash
genmedia assets characters list --json
```

   Found: record its `id` (step 4) and continue with section 4 instead of creating a duplicate.

2. Register the reference files in the Assets library, one call per file, best first, 20 at most. Read `asset.vector_id` from each response:

```bash
genmedia assets upload .genmedia/characters/mara/refs/r1-face.png --prompt "Mara, face reference, front view" --json
```

3. Create the character with those IDs (repeat `--reference_image`; an `--idempotency_key` makes a retry safe):

```bash
genmedia assets characters create "Mara" --description "<anchor>" --identifier mara --reference_image <vector_id_1> --reference_image <vector_id_2> --idempotency_key mara-create-1 --json
```

4. Read `character.id` from the response and store it:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" set-mirror mara --character-id "<character id>"
```

Notes:
- Flags of `genmedia assets ...` are plain strings (they are not JSON-parsed like model parameters), but multi-value flags split on commas: never put a comma inside a `--reference_image` value.
- A `request_id` can stand in for a `vector_id` when the reference came from a generation in this account and that request produced exactly one image. With several outputs per request it is undefined which image is taken: use `assets upload` and the `vector_id` instead.
- The identifier is taken by another entity: create the mirror with a suffixed identifier, tell the user which one, keep the local handle unchanged.

## 4. Keep it in sync

Sync only after a change the user would want to see in fal (new anchor, changed reference set), not after every generation.

```bash
genmedia assets characters update <character_id> --description "<anchor>" --reference_image <vector_id_1> --reference_image <vector_id_2> --json
```

- `--reference_image` on `update` replaces the whole set. Send the full list, not the delta.
- Register new reference files with `assets upload` first (step 2 above).
- The identifier cannot be updated. A renamed handle means a new character.
- Then refresh the timestamp: `character.py set-mirror <handle> --character-id <same id>`.
- Optional filing of results under the character: `genmedia assets collections add <character_id> --request_id <request_id> --json` (a character is a collection of type `character`). If it errors, skip it; it is bookkeeping, not identity.
- Mirror removed by the user in the web UI: `character.py set-mirror <handle> --clear`. This skill never deletes Assets entities.

## 5. Import a character that exists only in fal Assets

When the user made a character in fal's web UI and wants it here:

1. `genmedia assets characters list --json`, pick the entry whose `character_identifier` or `name` matches. Several matches: list them and let the user choose (import is a creation flow, so this uses its question budget).
2. Take `name`, `description`, `character_identifier` and `reference_images[]` (URLs).
3. Download each reference image into a temporary folder, then:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" init mara --name "Mara" --description "<description from fal>"
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" add-ref mara ./tmp/ref1.png --role face --cdn-url "<its fal url>"
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" set-mirror mara --character-id "<id>"
```

4. Assign roles by looking at each image. Rewrite the description into a proper anchor (`references/character-sheet.md`) if it contains shot variables, and tell the user you did.
5. Real person: the consent question still applies before the first generation.

## 6. What the mirror does not change

| Expectation | Reality |
|---|---|
| "Now `@mara` works in my prompts here" | No. This skill resolves handles locally with `character.py resolve`; the CLI never expands them. |
| "The mirror keeps my files alive" | No. A saved entity does not preserve an expired file. The durable copies are in `.genmedia/characters/<handle>/refs/`. |
| "Assets recognises my character in new images" | No. Browsing by character relies on recorded associations, not on visual recognition. |
| "Mirroring improves likeness" | No. Likeness comes from the references, the anchor and the model (`references/consistency-playbook.md`). |
