# ADR-0010: Licence and public-text policy

- **Status:** Proposed
- **Date:** 2026-11-01
- **Decided by:** maintainer (pending)
- **Drafted by:** maintainer with an AI agent

## Context

This repository is public. Its code and documents should be reusable, and nothing private should leak into it through text, history or configuration. A public repository leaks in predictable ways: a personal email in commit metadata, a credential or state file committed once and deleted later (it stays in history), an internal hostname or private path pasted into a document, or a copied paragraph from someone else's article.

## Options

### Licence

- **Apache-2.0 for everything:** permissive, with an explicit patent grant. One licence for code and docs keeps it simple.
- **Apache-2.0 for code, CC BY 4.0 for docs:** the more conventional split for prose, requiring attribution when the docs are reused.
- **MIT:** permissive, shorter, no patent grant.

### Leak prevention

- **Review only:** relies on attention, which fails eventually.
- **Automated checks before push and in CI:** a secret scanner over the full history, and a text check for private identifiers.

## Decision

**Apache-2.0 for the whole repository.**

**Public-text rules:**

- **Commit identity** is the maintainer's GitHub no-reply address, set in the repository's local git config.
- **No credentials, state files or environment files,** ever. TruffleHog scans the full history before every push (a pre-push hook in `.githooks/`) and in CI.
- **No private identifiers:** private repository names, internal hostnames, private work-tracker IDs, local file paths or personal email addresses. `tools/check_public_text.py` checks every tracked file for generic patterns. A private list of exact terms is kept outside the repository: in a git-ignored local file, and in a CI secret.
- **AI assistance is disclosed** in the README and in the agent trailers that [AGENTS.md](../../AGENTS.md) lists (`Co-Authored-By`, `Assisted-by`, `Agent-Effort`) on the commits an agent helped write. Session links and other trailers stay out of public commits.
- **Other people's writing is paraphrased and cited, never reproduced.** Reading notes summarise a source's claim and mechanism in their own words and link to it.
- **History starts fresh.** The repository never imports another repository's history.

## Lab stance and production stance

- **Lab stance:** the checks are cheap and run on every push, so the policy doesn't depend on remembering it.
- **Production stance:** companies run the same layers at larger scale: push protection, secret scanning, pre-publication review for open-source releases, and a contributor licence agreement or DCO for outside contributions. Outside code contributions aren't solicited here, so no DCO is required.

## Consequences

- A push fails if TruffleHog finds a likely secret, or if the text check finds a private identifier. A false positive is fixed by changing the text or narrowing the pattern, never by skipping the hook.
- Secret scanning and push protection on GitHub only become available once the repository is public, so until then the local hook is the only scanner.
- When something gets through anyway, [leak response](../leak-response.md) says what to do. Most of it can't be recalled once public, which is why the checks run before the push.

## What would change my mind

If someone wants to reuse the documents and the licence gets in the way, or if contributions from others start arriving, revisit the docs licence and the DCO.

## How we'd know

A leak, or a near miss caught only by review rather than by a check. Either one adds a pattern to the check in the same change that fixes it.
