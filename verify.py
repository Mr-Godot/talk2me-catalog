#!/usr/bin/env python3
"""Check that manifest.signed.json really is manifest.json, signed by the published key.

    pip install cryptography
    python verify.py

Three checks, and a non-zero exit on any of them:

  1. The envelope's payload is manifest.json BYTE FOR BYTE. Editing the manifest without re-signing
     is the easy mistake, and it fails silently: apps keep serving the old catalog while this
     repository shows the new one.
  2. The envelope's version field agrees with the payload's. That is what a hand-edited envelope
     looks like.
  3. The signature verifies against catalog-public-key.txt, using the same algorithm the app uses:
     ECDSA P-256 over SHA-256, signature in IEEE P1363 form (raw r||s, 64 bytes).

This needs no private key, so it is safe on any runner, including a fork's.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.exceptions import InvalidSignature

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest.json"
SIGNED = HERE / "manifest.signed.json"
PUBLIC_KEY = HERE / "catalog-public-key.txt"

ALGORITHM = "ecdsa-p256-sha256"


def fail(message: str) -> None:
    print("FAILED: " + message, file=sys.stderr)
    sys.exit(1)


def main() -> None:
    for path in (MANIFEST, SIGNED, PUBLIC_KEY):
        if not path.exists():
            fail(f"{path.name} is missing.")

    manifest_bytes = MANIFEST.read_bytes()
    envelope = json.loads(SIGNED.read_text(encoding="utf-8"))

    if envelope.get("algorithm") != ALGORITHM:
        fail(f"the envelope says algorithm {envelope.get('algorithm')!r}, expected {ALGORITHM!r}.")

    payload = base64.b64decode(envelope["payload"])
    if payload != manifest_bytes:
        fail(
            "manifest.json was changed without re-signing.\n"
            "manifest.signed.json carries different bytes, so apps would keep serving the old\n"
            "catalog while this repository shows the new one.\n"
            "Re-sign in the talk2me repo:  python catalog/sign.py"
        )

    payload_version = json.loads(payload)["version"]
    if envelope.get("version") != payload_version:
        fail(
            f"the envelope says version {envelope.get('version')} and the payload says "
            f"{payload_version}."
        )

    key = serialization.load_der_public_key(
        base64.b64decode(PUBLIC_KEY.read_text(encoding="utf-8").strip()))
    if not isinstance(key, ec.EllipticCurvePublicKey):
        fail("catalog-public-key.txt is not an elliptic curve public key.")

    raw = base64.b64decode(envelope["signature"])
    if len(raw) != 64:
        fail(f"the signature is {len(raw)} bytes, expected 64 (P-256 r||s).")

    half = len(raw) // 2
    der = utils.encode_dss_signature(
        int.from_bytes(raw[:half], "big"), int.from_bytes(raw[half:], "big"))

    try:
        key.verify(der, payload, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        fail("the signature does not verify against catalog-public-key.txt.")

    print(f"OK: manifest version {payload_version}, signed by {envelope.get('keyId')}, "
          f"payload matches manifest.json byte for byte.")


if __name__ == "__main__":
    main()
