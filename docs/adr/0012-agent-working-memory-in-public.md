# ADR-0012: Keep the agents' working memory in public

- **Status:** Proposed
- **Date:** 2026-11-06
- **Decided by:** maintainer (pending)
- **Drafted by:** maintainer with an AI agent

## Context

This repository is built in public: its decisions, designs and measured results all live here. AI agents do much of the drafting and implementation. They work from context that says where the project stands, what has been decided and how recurring tasks are done. Today that context lives outside the repository. Readers see the outputs but not the working state behind them, and an agent launched in a fresh clone starts without it. Several agent tools keep this kind of context as Markdown files in the repository they work on; this record decides whether this one can.

Two things make it hard:

- **Some context can't be public.** That covers the private terms the public-text check guards ([ADR-0010](0010-licence-and-public-text-policy.md)) and everything they protect: personal details and anything outside this project. It also covers infrastructure identifiers, such as machine inventories, cloud account IDs and network names, and reasoning unrelated to the design. The deny-list itself is the most sensitive item, because publishing it would reveal exactly what it hides.
- **Context that agents follow is an instruction surface.** Anyone can open an issue or a pull request on a public repository. If that text reaches the agents' memory unreviewed, it steers agents that can open pull requests and, from Phase 5, run cloud environments.

## Options

### Option A: All agent context private

Safe. But it hides the process that working in public is meant to show, and agents launched here start cold.

### Option B: All agent context public

Impossible: the deny-list and the identifiers have to stay private.

### Option C: Public working memory in this repository, with a small private remainder

The working state, procedures and agent roster live here and go through the same pull requests, checks and review as the work they describe. The private remainder stays outside the repository and in git-ignored local files.

### Option D: Public memory in a separate public repository

It keeps this repository's history free of memory updates. But the memory and the work it describes land in different pull requests and drift apart, and the checks have to exist twice.

## Decision

Option C. A `.agents/` directory holds:

- `context/active.md`: where the project stands. The phase, what's in flight, the next steps and the open questions. It's kept short and rewritten, never appended to.
- `context/progress.md`: what's done in each phase, linked to pull requests, experiment reports and decision records.
- `context/lessons.md`: each class of defect found, and the check that now prevents it.
- `seats.md`: which agents, models and effort levels do which kinds of work. It's the source for the commit trailers in [AGENTS.md](../../AGENTS.md).
- `handoffs/`: the prompts agents work from, each linked to its issues.
- `skills/<name>/SKILL.md`: procedures for recurring tasks. Examples: write a slice design doc, run an experiment, propose a decision record, move a component up the fidelity ladder, open a pull request, update this memory. They use the Agent Skills format, which Codex reads from `.agents/skills`; `.claude/skills` is a link to the same directory.

These rules come with it:

- A memory update goes in the same pull request as the work it describes.
- The public-text check and the secret scan cover `.agents/` like every other path.
- Agents load memory and skills only from `main`. Only the maintainer merges a change under `.agents/`, and a pull request touching it from anyone other than the maintainer or the agents' GitHub App is closed unmerged.
- Text from issues, pull request comments or other outside sources is never copied into memory as an instruction. Memory records the maintainer's decisions and the agents' findings, with links to where they came from.
- Memory never records personal details, other projects, employers, infrastructure identifiers or session links.

## Lab stance and production stance

- **Lab stance:** the process becomes inspectable. A reader can see what the agents were told, what they knew and how that context changed with each result. Any agent launched in a clone has what it needs.
- **Production stance:** teams already keep agent instructions in the repository (instruction files, rules, skills). Operational memory that holds customer or incident details goes in access-controlled systems. The same split by sensitivity applies here, with a different line.

## Consequences

- There are two places to update, with a rule for which gets what. The private remainder should stay small and change rarely.
- Memory is now an attack surface. Main-only loading and maintainer-only merges under `.agents/` are the defence.
- Nearly every pull request touches `context/active.md`. Keeping the files short keeps the diffs readable.
- Readers see unfinished thinking and wrong predictions. That's what working in public means here. Personal self-assessment still isn't recorded.

## What would change my mind

- A leak the public-text check missed. The kind of content that leaked moves to the private remainder, and a new check covers it.
- Memory diffs crowding out review. Progress then moves into pull request descriptions, and only `context/active.md` stays.

## How we'd know

- Nothing private ever reaches `main`, and each catch on a pull request is recorded in `context/lessons.md`.
- At each phase boundary, an agent launched cold in a fresh clone can state the current phase, the next step and the open questions from `.agents/` alone.
