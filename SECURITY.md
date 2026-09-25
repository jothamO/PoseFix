# Security Policy

PoseFix is pre-release software. Security reports are welcome.

## Please report privately

Do not open a public issue for:

- exposed API keys or credentials;
- remote code execution or command injection;
- unsafe file handling or path traversal;
- vulnerabilities that expose private images or generated outputs;
- dependency vulnerabilities with a concrete exploit path.

Until a dedicated security inbox is published, use GitHub's private vulnerability reporting feature when available for this repository. If that feature is unavailable, contact the repository owner privately through GitHub before disclosing details publicly.

## Secrets

PoseFix expects provider credentials to come from environment variables or an external secret store. Never commit API keys, tokens, `.env` files, or private provider credentials.

## Supported versions

Before the first stable release, only the latest code on the default branch and the latest tagged pre-release are expected to receive security fixes.
