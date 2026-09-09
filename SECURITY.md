# Security Policy

## Supported Versions

Security updates are actively provided for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

---

## Reporting a Vulnerability

We take the security of the **EDGE Content Engine** and its automated pipeline seriously.

If you believe you have discovered a security vulnerability (such as API credential leakage, unauthorized command injection via agent prompt evaluation, AST execution escaping, or infrastructure vulnerabilities):

1. **Do NOT open a public GitHub issue.**
2. Send an email to `security@chittineni.dev` (or report confidentially via GitHub Security Advisories).
3. Include:
   - Type of issue (e.g. prompt injection vulnerability, arbitrary code execution in validator sandbox, secret exposure)
   - Step-by-step instructions to reproduce the vulnerability
   - Proof of concept payload or minimal reproduction code
   - Potential impact of the vulnerability

### Response Timeline
- **Initial Acknowledgment**: Within 24 hours
- **Severity Assessment & Triage**: Within 48 hours
- **Fix & Patch Deployment**: Targeted within 5-7 business days depending on severity

---

## Security Best Practices for Maintainers & Contributors

- **Never Commit Secrets**: Do not commit `.env` files, production API tokens, private keys, or AWS secrets. The `.gitignore` and `.pre-commit-config.yaml` enforce this locally.
- **LLM Prompt Injection Defense**: Prompts accepting external GitHub diffs or third-party web content must delimit inputs clearly and validate downstream AST before execution.
- **Dependency Auditing**: All pull requests are screened by `pip-audit` and Dependabot to prevent vulnerable supply chain packages from being introduced.
