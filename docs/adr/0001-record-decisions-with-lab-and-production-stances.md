# ADR-0001: Record decisions as MADR, with a lab stance and a production stance

- **Status:** Proposed
- **Date:** 2026-11-01
- **Decided by:** maintainer (pending)
- **Drafted by:** maintainer with an AI agent

## Context

This repository makes many deliberate choices that a real team wouldn't: nine languages, eight data stores, three brokers. Without written reasoning, that variety reads as sprawl. Demo systems that kept their reasoning outside the repository, in a book or a separate site, lost it when the two drifted apart. The decisions also have to survive questioning: each one should be defensible from its own text.

## Options

### Option A: No formal records; reasoning in design docs

Cheap, but decisions that span slices (the language policy, the platform contract) have no home, and superseded decisions vanish.

### Option B: Nygard-style ADRs (context, decision, consequences)

The classic minimal format. It has no place for rejected options or for how a decision would be proven wrong.

### Option C: MADR, extended

[MADR](https://adr.github.io/madr/) adds considered options and their trade-offs to the classic format. This repository extends it with three fields: a **lab stance and a production stance**, **what would change my mind**, and **how we'd know** (the metric or experiment that would show the decision is wrong).

## Decision

Option C. Records live in `docs/adr/`, numbered, written from the [template](../templates/adr.md). A record is never edited to reverse its decision; a new record supersedes it, and the old one's status links forward. Each record names who decided it and who drafted it.

## Lab stance and production stance

- **Lab stance:** the two extra fields are the point. "Lab stance versus production stance" turns variety into judgment, and "how we'd know" ties each decision to something measurable.
- **Production stance:** the same. Real teams that write ADRs benefit most from the rejected options and the reversal criteria, which are the parts most often skipped.

## Consequences

- Every cross-cutting choice gets a record before implementation starts.
- Records are short. A record that needs more than two pages is probably a design doc.
- The maintainer decides each record; an agent may draft it.

## What would change my mind

If records go stale because nobody revisits them when experiments contradict them, they become fiction. Then the format is not the problem, the process is.

## How we'd know

Every experiment report's "what changed" section names the record or design doc it touched. An experiment that contradicts a record without a superseding record is a process failure, and review catches it.
