# Part 5 — Development history

Repository: git@github.com:SubramDas/room-proof.git  
Submission branch: final_implementation

Eight incremental development commits were recorded during pipeline implementation, from environment setup through sensor decoding, structural geometry, RGB pose changes, benchmarking, validation and runtime recovery. Later commits record the ceiling fix, submission packaging and supplied consumer-app evidence at their actual commit times. No commit dates or earlier declarations were rewritten to imply work happened earlier.

## Storage and identity

The coding environment exposed .git as an empty read-only directory. Development used Git's alternate metadata directory .history, with the project as its work tree. This is standard Git history and is exported as a portable bundle. A normal clone of the remote branch uses a regular .git directory and ordinary git commands.

Earlier commits use the local identity `Astra implementation <astra@local.invalid>`. This identifies the automated development environment, not a verified human author. AI assistance was used; the evaluator can inspect actual commits and diffs. Some large implementation steps were grouped, and not every intermediate working-tree edit was separately committed. Commit count alone is not proof of process quality.

## Inspect and reproduce the history

```bash
git clone --branch final_implementation git@github.com:SubramDas/room-proof.git
cd room-proof
git log --reverse --date=iso-strict --format='%h %ad %an %s'
git show --stat e3977de
git diff e3977de..final_implementation -- astra/
```

Offline alternative, using Part 5's development.bundle:

```bash
git clone -b final_implementation development.bundle room-proof
git -C room-proof log --oneline --reverse
```

Raw data/models/ZIPs are separate artifacts. Read docs/SUBMISSION_INDEX.md for evidence excerpts and limitations. Bundle integrity, history export and the pushed branch commit are recorded in the Part 5 submission directory.
