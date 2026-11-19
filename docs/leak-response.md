# When private text gets in

The checks in [ADR-0010](adr/0010-licence-and-public-text-policy.md) try to stop private text before it's pushed. This page is for when something gets through anyway: into a commit, a pull request, an issue, a comment or the agents' memory ([ADR-0012](adr/0012-agent-working-memory-in-public.md)). If you aren't the maintainer and you've found something, report it privately as [SECURITY.md](../SECURITY.md) says, and don't quote it in public.

## The rule underneath

Anything that reached the public repository, even for a minute, may already be copied: by forks, clones, notification emails, event archives and scrapers. Removing it limits who sees it from then on, but doesn't recall it. So the response has three parts: make the leaked thing useless where that's possible, remove it from what GitHub serves, and add a check so the same kind of text can't get through again.

## First: what leaked

| What | Examples | What actually fixes it |
|---|---|---|
| A credential | A token, a key, a password | Revoke or rotate it at once, before anything else. That is the fix. Removing it from history is clean-up, and GitHub's guide says it may not be needed |
| An identifier for something that exists | A cloud account ID, a hostname, an address, a network name | Replace the thing when that's cheap (a new sandbox account, a renamed machine), so the leaked identifier points at nothing. Otherwise remove it, and check what the identifier exposes |
| Personal or off-project text | A name, an employer, another project, a private plan | Remove it. It can't be made useless, so speed and how far it spread matter most |
| The private-term list, or much of it | | The worst case, because it exposes everything it guards at once. Treat each term as its own leak of one of the kinds above |

## Then: where it got to

| Where | Who could see it | What to do |
|---|---|---|
| A local commit the hook stopped | Nobody | Fix the commit (amend it, or rebase to edit it) and push again. Nothing else |
| Anywhere, while the repository is still private | The maintainer | Rewrite history freely. This is the cheapest time to fix anything, which is why the whole history is scanned before the repository goes public |
| A pushed branch or an open pull request | Everyone | Close the pull request and delete the branch, then push the fixed work on a new branch. The old commits stay reachable by their hash and through the closed pull request, which only GitHub Support can remove; ask them when the content matters |
| `main` | Everyone, and every clone | Push a fix that removes it the same day. When it matters, also [rewrite history](#rewriting-history-on-main) |
| A pull request title or body, an issue or a comment | Everyone, and everyone notified by email | Edit the text out. For a comment, also delete the old revision from its edit history; the edit's author and time stay visible, but its content doesn't. A renamed title stays in the timeline, so a leaked title means deleting the issue, or asking GitHub Support about a pull request. Only the maintainer's account can delete an issue, and nobody but Support can delete a pull request. A merged pull request's title and body are also the squash commit's message on `main`, so the row above applies too |
| The agents' memory under `.agents/` | As for `main` or a branch | As above, fixing `main` first, because agents load memory only from `main`. Then search the handoffs and skills for copies of the same text, and restart any agent that loaded it |

### Rewriting history on main

Follow GitHub's [guide to removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository). In short:

1. Rotate first if it's a credential.
2. In a fresh clone, run `git filter-repo --sensitive-data-removal` (version 2.47 or later) with `--replace-text` for a phrase, or `--invert-paths --path` for a file. Check the result with the public-text check over the whole history.
3. Force-push every branch with `git push --force --mirror origin`. Pull request refs refuse the push; that's expected.
4. Ask GitHub Support to dereference the affected pull requests, remove cached views and run garbage collection. Give them the first changed commit and the number of affected pull requests from the filter-repo output, not the leaked text.
5. Delete every other working copy, agents' worktrees included, and clone again. An old clone pushed later puts the text back.
6. Ask the owner of any fork to delete or rewrite it. GitHub doesn't touch forks.

It costs something: every commit hash after the leak changes, so links to commits from reports, issues and decision records break. It's worth it for personal text, a credential that can't be rotated, or an identifier for something that can't be replaced. For a minor slip, the fix and a new check are enough.

## Afterwards: leave a check behind

- In the same change as the fix, add a pattern to `tools/check_public_text.py`, or the term to the private list (the local file and the CI secret), and confirm it catches the original text. A slip that only a reader could catch gets a rule in [AGENTS.md](../AGENTS.md) or a skill instead.
- Record the class in `.agents/context/lessons.md`: what kind of text it was, the path it took, which check missed it and why, and the new check. Never repeat the leaked text there, in the fix's commit message or pull request, or anywhere else public.
- The details (exactly what leaked, where, and the Support ticket) stay with the maintainer, outside the repository.

## Why most of the work comes before the push

Removal can't recall anything, so the checks that count run before text is public:

- The pre-push hook runs TruffleHog and the public-text check on every commit it pushes.
- Text posted to GitHub (pull request titles and bodies, issues and comments) is written to a file, checked with `tools/check_public_text.py --text <file>`, and then posted from the file (`gh pr create --body-file`). CI's check of a pull request's title and body runs after the pull request is already public, so it's a backstop, not the guard.
- Once the repository is public, GitHub's push protection blocks known secret formats on GitHub's side, before a push lands.
- A change under `.agents/` gets a cold read before it's pushed. An agent started without the private context reads only the diff, and flags anything about a person, another project or a place. The term list can't catch a private fact written in new words, and memory is where an agent that has seen private context is most likely to write one.
- The maintainer reviews and merges every change under `.agents/`.

The public-text check prints only a label such as `private term`, never the text it matched, so a failing check in CI doesn't publish what it found.

## Before the repository goes public

- Run the public-text check and TruffleHog over the whole history.
- Turn on secret scanning and push protection.
- Set the `PUBLIC_TEXT_DENYLIST` secret, so CI loads the private terms.
- Turn on private vulnerability reporting, which [SECURITY.md](../SECURITY.md) points to.
