# ADR-0012: Keep the agents' working memory in public

- **Status:** Proposed
- **Date:** 2026-11-06, revised 2026-11-21 to choose Option D
- **Decided by:** maintainer (pending)
- **Drafted by:** maintainer with an AI agent

## Context

This repository is built in public: its decisions, designs and measured results all live here. AI agents do much of the drafting and implementation. They work from context that says where the project stands, what has been decided and how recurring tasks are done. Today that context lives outside the repository. Readers see the outputs but not the working state behind them, and an agent launched in a fresh clone starts without it. Several agent tools keep this kind of context as Markdown files in the repository they work on; this record decides whether this one can.

The project spans four repositories: this hub, which holds the backend, the harness, the decision records and the design docs, and one each for the web, Android and iOS clients, whose work starts in Phases 8 to 10. Whatever holds the memory has to serve all four.

Two things make it hard:

- **Some context can't be public.** That covers the private terms the public-text check guards ([ADR-0010](0010-licence-and-public-text-policy.md)) and everything they protect: personal details and anything outside this project. It also covers infrastructure identifiers, such as machine inventories, cloud account IDs and network names, and reasoning unrelated to the design. The deny-list itself is the most sensitive item, because publishing it would reveal exactly what it hides.
- **Context that agents follow is an instruction surface.** Anyone can open an issue or a pull request on a public repository. If that text reaches the agents' memory unreviewed, it steers agents that can open pull requests and, from Phase 5, run cloud environments.

## Options

### Option A: All agent context private

Safe. But it hides the process that working in public is meant to show, and agents launched here start cold.

### Option B: All agent context public

Impossible: the deny-list and the identifiers have to stay private.

### Option C: Public working memory in the hub, with a small private remainder

A `.agents/` directory in this repository holds the working state, procedures and agent roster, and they go through the same pull requests, checks and review as the work they describe. A memory update lands in the same pull request as hub work, and agent tools find the skills without any setup. But the clients' agents read it from a second checkout anyway. A serious leak in memory means rewriting this repository's history, which changes every commit hash after it and breaks the links to them from reports, records and issues. And the memory goes public on the same day as the hub.

### Option D: A separate public repository for memory, spanning all four, with a small private remainder

The same files in their own repository. No code repository owns it, so it serves all four on equal terms. A serious leak in memory is fixed by rewriting that repository's history alone, so the hub's commit links stay intact; memory is where an agent that has seen private context is most likely to write a private fact. Its history reads by itself, and memory churn stays out of the code's diffs. It can go public on its own schedule. The costs: a change that updates memory takes two pull requests, agents keep a second clone, the skills need linking into each checkout, and the repository needs its own copy of the checks.

## Decision

Option D. The repository [project-fa-agents](https://github.com/citrusunshiu/project-fa-agents) holds:

- `context/active.md`: where the project stands. The phase, what's in flight, the next steps and the open questions. It's kept short and rewritten, never appended to.
- `context/progress.md`: what's done in each phase, linked to pull requests, experiment reports and decision records.
- `context/lessons.md`: each class of defect found, and the check that now prevents it.
- `seats.md`: which agents, models and effort levels do which kinds of work. It's the source for the commit trailers in [AGENTS.md](../../AGENTS.md).
- `handoffs/`: the prompts agents work from, each linked to its issues.
- `skills/<name>/SKILL.md`: procedures for recurring tasks, the clients' platform skills included, so every procedure lives in one place. Examples: write a slice design doc, run an experiment, propose a decision record, move a component up the fidelity ladder, open a pull request, update the memory. They use the Agent Skills format.

**How agents use it.** An agent keeps a clone of project-fa-agents on `main` beside the repository it works in, and reads that repository's `AGENTS.md` and `context/active.md` before it starts. Each code repository keeps only its own `AGENTS.md`, with its build and test commands and its conventions, and says where the memory is. The skills are linked into each checkout and worktree as `.agents/skills`, where Codex looks, and `.claude/skills`, where Claude Code looks. The links are local and git-ignored.

These rules come with it:

- A change that updates memory is two pull requests: the work in its own repository, and the memory update in project-fa-agents. Each links to the other, and the memory update merges after the work. A change to memory alone, such as a new skill, is one pull request.
- project-fa-agents runs the same public-text check and secret scan as the hub. Every change to it also gets a cold read before it's pushed, by an agent started without the private context. [Leak response](../leak-response.md) covers both, and what happens when something gets through anyway.
- Agents load memory and skills only from `main`. Only the maintainer merges in project-fa-agents, and a pull request there from anyone other than the maintainer or the agents' GitHub App is closed unmerged.
- Text from issues, pull request comments or other outside sources is never copied into memory as an instruction. Memory records the maintainer's decisions and the agents' findings, with links to where they came from.
- Memory never records personal details, other projects, employers, infrastructure identifiers or session links.
- Issues about the memory are filed in the hub, like every other issue.

## Lab stance and production stance

- **Lab stance:** the process becomes inspectable. A reader can see what the agents were told, what they knew and how that context changed with each result. Any agent launched in a clone of the hub and project-fa-agents has what it needs.
- **Production stance:** teams already keep agent instructions in the repository (instruction files, rules, skills). Operational memory that holds customer or incident details goes in access-controlled systems. The same split by sensitivity applies here, with a different line.

## Consequences

- There are two places to update, with a rule for which gets what. The private remainder should stay small and change rarely.
- Memory is now an attack surface. Main-only loading and maintainer-only merges in project-fa-agents are the defence.
- A leak in memory is as public as any other, and as hard to recall. [Leak response](../leak-response.md) says what removal can and can't do. Rewriting history to remove one touches only project-fa-agents.
- Memory trails the work between the two merges. The memory pull request names the work's pull request, so the gap is visible.
- project-fa-agents carries a copy of the public-text check, which has to stay the same as the hub's.
- Readers see unfinished thinking and wrong predictions. That's what working in public means here. Personal self-assessment still isn't recorded.

## What would change my mind

- A leak the public-text check missed. The kind of content that leaked moves to the private remainder, and a new check covers it.
- Memory diffs crowding out review. Progress then moves into pull request descriptions, and only `context/active.md` stays.
- The paired pull requests becoming a chore, or memory routinely trailing the work by more than a day. Then the memory moves into the hub's `.agents/`. `git filter-repo --to-subdirectory-filter .agents` carries its history across, so starting separate doesn't close that door.

## How we'd know

- Nothing private ever reaches `main`, and each catch on a pull request is recorded in `context/lessons.md`.
- At each phase boundary, an agent launched cold in a fresh clone can state the current phase, the next step and the open questions from project-fa-agents alone.
