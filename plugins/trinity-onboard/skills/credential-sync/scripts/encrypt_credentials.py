#!/usr/bin/env python3
"""
Encrypt local credential files to .credentials.enc

Usage:
    export CREDENTIAL_ENCRYPTION_KEY=<your-key>
    python encrypt_credentials.py

Or get key from Trinity:
    CREDENTIAL_ENCRYPTION_KEY=$(curl -s ... get_credential_encryption_key | jq -r '.key')
"""

import json
import os
import sys
from base64 import b64encode

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


def collect_files():
    """Collect credential files to encrypt."""
    files = {}

    # Required: .env
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            files['.env'] = f.read()
        print(f"  Found .env ({len(files['.env'])} bytes)")
    else:
        print("WARNING: No .env file found")

    # Optional: .mcp.json
    if os.path.exists('.mcp.json'):
        with open('.mcp.json', 'r') as f:
            files['.mcp.json'] = f.read()
        print(f"  Found .mcp.json ({len(files['.mcp.json'])} bytes)")

    return files


def encrypt(key: bytes, files: dict) -> bytes:
    """Encrypt files dict to bytes using AES-256-GCM."""
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    plaintext = json.dumps(files).encode('utf-8')
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ciphertext


def main():
    print("Encrypting credentials...")
    print()

    key = get_key()
    files = collect_files()

    if not files:
        print("ERROR: No files to encrypt")
        sys.exit(1)

    encrypted = encrypt(key, files)

    output_path = '.credentials.enc'
    with open(output_path, 'wb') as f:
        f.write(encrypted)

    print()
    print(f"Encrypted {len(files)} file(s) to {output_path}")
    print(f"  Size: {len(encrypted)} bytes")
    print()
    print("This file is safe to commit to git.")
    print("To restore: python decrypt_credentials.py")


if __name__ == '__main__':
    main()
