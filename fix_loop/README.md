# Scored fix loop

This directory contains the protocol and declaration template only. No
baseline exists yet. Do not populate the declaration with invented numbers.

1. Freeze raw capture hashes, independent truth, scorer code revision, every
   baseline plan, and all gate values.
2. If execution/schema fails, select that blocker first. Otherwise use
   `roomproof.fix_selection.rank_failed_gates`: largest relative threshold gap,
   then affected count, then alphabetical gate ID.
3. Write a dated declaration using `declaration_template.md` and **commit it
   before editing the declared fix**.
4. Implement and commit the fix. Rerun the same inputs, truth, and scorer; use
   paired controlled recaptures only for a protocol change.
5. Save before/after run manifests, code diff, plans, gate table, prediction
   error, and regressions. Report failures and any changed external scorer.
