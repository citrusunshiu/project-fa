# Rulesets

The rulesets each repository runs, kept here so a change to them is reviewed like any other change ([#5](https://github.com/citrusunshiu/project-fa/issues/5)). The maintainer applies them: the agents' App has no administration access.

| File | Applies to | What it does |
|---|---|---|
| `integrity-hub.json` | project-fa | `main` can't be deleted or force-pushed and keeps a linear history, and the `docs` and `secrets` checks must pass. Nobody can bypass it. |
| `integrity-memory.json` | project-fa-agents | The same, with the `text` and `secrets` checks. |
| `integrity-client.json` | project-fa-web, project-fa-android, project-fa-ios | The same, without required checks until the clients have CI. |
| `review.json` | all five | Changes reach `main` only through a squash-merged pull request, with an approval given after its last push, and the code owner's approval on the paths `.github/CODEOWNERS` assigns. The maintainer can bypass it on a pull request, for the maintainer's own. |

To create a ruleset: `gh api -X POST repos/citrusunshiu/<repository>/rulesets --input .github/rulesets/<file>`. To change one, `PUT` to `repos/citrusunshiu/<repository>/rulesets/<id>` with the same file.

A history rewrite ([leak response](../../docs/leak-response.md#rewriting-history-on-main)) needs the integrity ruleset switched off while the force-push runs, and back on straight after.
