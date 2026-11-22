# project-fa

The backend of Project FA, a made-up delivery company, designed on paper, partly built, load-tested and broken on purpose, with the reasoning and the measured results kept side by side.

## What this is

A study project in distributed systems. Project FA is fictional; the design questions are real. Every component exists first as a design document, then as a simulated service doing fake work, and only the parts worth learning get a real implementation. The whole system can run and show where it bottlenecks long before most of it is written.

The output is the experiment. Each one states a hypothesis with a number in it, predicts the result before the run, runs as a pipeline that creates an environment, loads it, injects a fault, checks the result against committed baselines and tears everything down, and then records what changed in the design because of it.

## What this is not

- Not a product. It has no real users, real payments or personal data.
- Not a production-scale claim. Lab numbers come from a laptop and short-lived cloud environments, and every report says which scale it measured.
- Not a framework for others to adopt, although you're welcome to read it, borrow from it and open issues.

## Status

**Phase 0: paper architecture.** Nothing runs yet. Phase 0 ends when the charter, company brief, component catalog and founding decision records read as one coherent design. The roadmap is in the [charter](docs/charter.md#roadmap).

## Reading order

1. [Charter](docs/charter.md): purpose, non-goals, the fidelity ladder, what results may claim.
2. [Company brief](docs/company/brief.md): what Project FA does, the features and the problem each one forces, and the paper-scale estimates.
3. [Architecture overview](docs/architecture/overview.md), the [platform contract](docs/architecture/platform-contract.md) every service meets, and the [environments](docs/architecture/environments.md) it runs in: a laptop, owned machines, AWS, GCP, Azure, or a split across them.
4. [Decision records](docs/adr/README.md): why each choice was made, with a lab stance and a production stance.
5. [Component catalog](catalog/components.yaml): every component, its fidelity level, language, stores and design doc.

## How the system gets built

| Level | What exists |
|---|---|
| F0 Paper | A design doc: requirements, estimates, API, data model, failure table, open questions |
| F1 Simulated | A generic simulator plays the component from a topology file: latency, CPU cost, fan-out, pools, retries |
| F2 Real path | A real implementation of the core path, on a real data store, meeting the platform contract |
| F3 Hardened | F2 plus SLOs, burn-rate alerts, a runbook and a chaos suite that passes |

## Repository map

```
docs/
  charter.md         purpose, non-goals, fidelity ladder, claims policy, roadmap
  leak-response.md   what to do when private text gets into the repository
  company/           product brief, estimates, SLO drafts
  architecture/      context and container diagrams, platform contract, environments, costs
  adr/               decision records
  design/            design docs, one per slice of the system
  experiments/       experiment reports, written by the runs themselves
  reading/           notes on papers and engineering blogs, each changing something
  gamedays/          game days and postmortems
  templates/         templates for all of the above
catalog/             components.yaml, the source of truth for what exists
tools/               the checks CI runs on every change
```

Later phases add `sim/`, `services/`, `templates/`, `platform/`, `load/`, `chaos/`, `lab/` and `infra/`. The web, Android and iOS clients live in their own repositories: [project-fa-web](https://github.com/citrusunshiu/project-fa-web), [project-fa-android](https://github.com/citrusunshiu/project-fa-android) and [project-fa-ios](https://github.com/citrusunshiu/project-fa-ios). The agents' working memory has its own repository too: [project-fa-agents](https://github.com/citrusunshiu/project-fa-agents). Issues for all of them are filed here.

## How it's made

The maintainer drafts docs and code with AI coding agents. The maintainer decides every decision record, and answers each design doc's question chain before reading the model answers. Commits that an agent helped write say so in trailers naming the agent, its model and its effort level ([AGENTS.md](AGENTS.md)). What the agents work from, their state, procedures and roster, is public in [project-fa-agents](https://github.com/citrusunshiu/project-fa-agents) ([ADR-0012](docs/adr/0012-agent-working-memory-in-public.md)).

## Checks

```sh
tools/check.sh
```

This runs the catalog, link and public-text checks. It needs [uv](https://docs.astral.sh/uv/). The public-text check also looks for private terms from a list only the maintainer has; without it, run `tools/check.sh --allow-no-terms`.

## Licence

[Apache-2.0](LICENSE).
