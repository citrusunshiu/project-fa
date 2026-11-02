# ADR-0009: Terraform, kept compatible with OpenTofu

- **Status:** Proposed
- **Date:** 2026-11-01
- **Decided by:** maintainer (pending)
- **Drafted by:** maintainer with an AI agent

## Context

Cloud environments in this repository are short-lived: created for one experiment, destroyed after it, and reaped if anything is left behind. The infrastructure code has to be readable, widely understood, and runnable by anyone who clones the repository.

HashiCorp moved Terraform from the MPL to the Business Source License in August 2023. The community forked it as OpenTofu under the Linux Foundation, still MPL-licensed. IBM completed its acquisition of HashiCorp in early 2025. The two tools still share the HCL language and most providers, and have diverged in newer features.

## Options

### Option A: Terraform

The most widely used infrastructure-as-code tool, and the one most documentation and examples assume. The BSL restricts offering Terraform as a competing commercial service; it does not restrict using it.

### Option B: OpenTofu

Open source, community governed, with features Terraform lacks, such as client-side state encryption. Smaller ecosystem of documentation and hiring familiarity.

### Option C: Pulumi or the AWS CDK

Infrastructure in a general-purpose language. Powerful, but less common for this job, and the CDK is AWS-only.

## Decision

Terraform for the code and the documentation, written so that it also runs under OpenTofu: no features unique to either tool. A CI job validates the configuration with both. State lives in a remote backend with locking (S3 with native lock files on AWS) and never in git.

## Lab stance and production stance

- **Lab stance:** Terraform is what most readers know. Validating with OpenTofu as well keeps the code portable, and the licence change is a decision worth recording in its own right.
- **Production stance:** either tool is defensible. A company worried about vendor terms might pick OpenTofu; one buying HashiCorp's commercial products would stay on Terraform.

## Consequences

- Features unique to either tool (Terraform Stacks, OpenTofu's state encryption) are off limits while compatibility holds.
- Cloud credentials come from GitHub Actions through OIDC federation. No long-lived keys exist anywhere.
- Every resource carries a time-to-live tag, and a reaper deletes anything past it.

## What would change my mind

If the two tools diverge so far that keeping both green costs real effort, pick one. If Terraform's licence terms change again in a way that affects users, switch to OpenTofu.

## How we'd know

The dual-validation CI job starts failing on one tool and not the other.
