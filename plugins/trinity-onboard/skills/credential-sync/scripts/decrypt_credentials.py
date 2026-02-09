#!/usr/bin/env python3
"""
Decrypt .credentials.enc to restore credential files.

Usage:
    export CREDENTIAL_ENCRYPTION_KEY=<your-key>
    python decrypt_credentials.py

Or get key from Trinity:
    CREDENTIAL_ENCRYPTION_KEY=$(curl -s ... get_credential_encryption_key | jq -r '.key')
"""

import json
import os
import sys

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    print("ERROR: cryptography package not installed")
    print("Run: pip install cryptography")
    sys.exit(1)


def get_key():
    """Get encryption key from environment."""
    key = os.environ.get('CREDENTIAL_ENCRYPTION_KEY')
    if not key:
        print("ERROR: CREDENTIAL_ENCRYPTION_KEY environment variable not set")
        print()
        print("Get the key from Trinity:")
        print("  1. Via MCP: call get_credential_encryption_key tool")
        print("  2. Via API: GET /api/credentials/encryption-key")
        print()
        print("Then set it:")
        print("  export CREDENTIAL_ENCRYPTION_KEY=<key>")
        sys.exit(1)
    return bytes.fromhex(key)


def decrypt(key: bytes, encrypted: bytes) -> dict:
    """Decrypt bytes to files dict using AES-256-GCM."""
    nonce = encrypted[:12]
    ciphertext = encrypted[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext.decode('utf-8'))


def main():
    input_path = '.credentials.enc'

    if not os.path.exists(input_path):
        print(f"ERROR: {input_path} not found")
        print()
        print("To create encrypted credentials:")
        print("  1. Create .env with your credentials")
        print("  2. Run: python encrypt_credentials.py")
        sys.exit(1)

    print(f"Decrypting {input_path}...")
    print()

    key = get_key()

    with open(input_path, 'rb') as f:
        encrypted = f.read()

    try:
        files = decrypt(key, encrypted)
    except Exception as e:
        print(f"ERROR: Decryption failed - {e}")
        print("Check that CREDENTIAL_ENCRYPTION_KEY is correct")
        sys.exit(1)

    # Write files
    for filename, content in files.items():
        # Safety check - only allow specific files
        if filename not in ['.env', '.mcp.json', '.mcp.json.template']:
            print(f"  Skipping unexpected file: {filename}")
            continue

        # Warn if file exists
        if os.path.exists(filename):
            print(f"  Overwriting existing {filename}")

        with open(filename, 'w') as f:
            f.write(content)
        print(f"  Wrote {filename} ({len(content)} bytes)")

    print()
    print(f"Restored {len(files)} credential file(s)")
    print()
    print("SECURITY REMINDER:")
    print("  - .env is in .gitignore (don't commit)")
    print("  - .mcp.json may contain secrets (check .gitignore)")


if __name__ == '__main__':
    main()
