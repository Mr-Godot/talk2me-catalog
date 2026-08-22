# talk2me catalog

The list of speech providers and on-device models that [talk2me](https://github.com/Mr-Godot/talk2me)
offers, published as one signed file. Installed apps read it from this repository, so a new provider,
a new model, a corrected price or a revoked entry reaches every user without a new release.

## The files

| File | What it is |
|---|---|
| `manifest.json` | The catalog. Readable, diffable, and the only file a change is written in. |
| `manifest.signed.json` | The same bytes, base64, plus a signature. **This is the file the app fetches.** |
| `catalog-public-key.txt` | The public half of the signing key, for checking a signature yourself. |

The app fetches exactly one URL:

```
https://raw.githubusercontent.com/Mr-Godot/talk2me-catalog/main/manifest.signed.json
```

## What the app trusts

The signature, and nothing else. Not this repository, not GitHub, not TLS, not the file name.

- The public keys are compiled into the app. Bytes that do not verify against one of them are
  **discarded without being parsed**. There is no "trust anyway" path and no unsigned fallback.
- A catalog with a version older than the one already held is refused, so serving an old file cannot
  roll a user back to a revoked model.
- Every app ships a signed copy of the catalog inside the binary, so a fresh install with no network
  still has a full list. The download only ever replaces a verified copy with a newer verified copy.
- The catalog is data about models. It never carries code, and the app never executes anything from it.

That means a compromise of this repository, or of the account that owns it, cannot make an app trust
a bad catalog. It could only stop the catalog from updating. The signing key is not stored here, not
on any developer's disk, and not in CI: it lives in a password vault and is read into memory only for
the moment a manifest is signed.

## Verify it yourself

```bash
pip install cryptography
python verify.py
```

`verify.py` checks the three things that matter: the payload is `manifest.json` byte for byte, the
envelope's version agrees with the payload's, and the signature verifies against
`catalog-public-key.txt`. The same script runs on every pull request, so a manifest edited without
re-signing cannot land.

## Changing the catalog

Changes are made in the [talk2me](https://github.com/Mr-Godot/talk2me) repository, under `catalog/`,
which is the source of truth. `python catalog/sign.py` re-signs; `python catalog/sign.py --publish`
copies the verified pair here for a pull request.

Editing `manifest.json` here on its own does nothing: without a matching signature no app will read
it, and CI will fail the pull request.

## Privacy

The app sends no identity, no telemetry and no content with the fetch. It is a conditional GET for a
static file. A provider being listed here is not a claim that you should use it: each entry carries
what we know about that provider's data handling, in plain words, and the app always has a fully
local path that talks to nobody.
