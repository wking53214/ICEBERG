# RECOVERY

Raw artifacts recovered for the ICEBERG reconstruction. `REPORT.md` records
where each came from, with hashes. This file records how the two trees in
this repository relate, and which one to edit.

## Two archives, one day apart

`REPORT.md` documents both:

| archive | zip timestamp | entries | landed in |
| --- | --- | ---: | --- |
| `Iceberg_full_repo.zip` | 2026-07-01 18:53–18:54 | 123 | the organized tree (`Engines/`, `Domain/`, `API/`, …) |
| `Iceberg_flat.zip` | 2026-07-02 13:54 | 33 | `RECOVERY/flat/` |

`flat/` holds exactly 33 files, matching that archive entry for entry. It is
the archive verbatim, not a staging area.

**The flat archive is roughly nineteen hours newer than the full one.**

## What that meant

The reconstruction was assembled from the *earlier* archive. For five files
the two archives differ, and in every case the flat copy is the later,
corrected version, each carrying a `Fixed 2026-07-01` comment explaining
what it repairs:

| file | was | now |
| --- | ---: | ---: |
| `Engines/bayes_gpu.py` | 49 lines | 58 |
| `Engines/rl_ppo.py` | 59 lines | 98 |
| `Engines/rl_marl.py` | 46 lines | 86 |
| `Latent/LatentPayload.py` | 234 lines | 256 |
| `Sim/Simulator.py` | 113 lines | 167 |

The clearest case is `bayes_gpu.py`: the earlier version calls `.log()` on
unclamped probabilities, so `log(0)` yields `-inf`, and `-inf - (-inf)` inside
softmax's max-subtraction step yields `NaN`. The fix clamps to `1e-12` first.
Its own comment records the verification: for `posterior={A:0,B:1}` with
`likelihood={A:1,B:0}` the output was `{"A": nan, "B": nan}`, which breaks
determinism (`NaN != NaN`, so identical inputs compare unequal) and serialises
through `json.dumps` without error, letting a corrupted result reach a
structural hash looking like valid JSON.

Those five files have been brought forward. The organized tree now carries the
newer version of every file the two archives share.

## Which copy to edit

**The organized tree is authoritative.** `Engines/`, `Domain/`, `API/`,
`Model/`, `Registry/`, `SDK/`, `Sim/`, `Latent/`, `Governance/`, `Tests/`.

`RECOVERY/` is a preserved record and is not edited. It stays because it is
the evidence for what was recovered and from where, and because the divergence
above is only visible while both copies exist.

21 files under `flat/` are byte-identical to their counterpart in the
organized tree. 12 more exist only under `flat/` — `conftest.py`, the tier-0
stress tests, `test_cluster_runner.py`, `LEVER_REGISTRY_SPEC.md`,
`SCORECARD.md`, `TIER_0_1_VALIDATION_REPORT.md` and others — and have not been
placed in the tree because no counterpart exists to place them against.

## Other RECOVERY subdirectories

| directory | contents |
| --- | ---: |
| `pasted/` | 80 source artifacts recovered from the conversation corpus, all `role: user` |
| `corpus_artifacts/` | 16 |
| `gsa_adapter/` | 6 |
| `on_disk_copies/` | 4 |

`pasted_manifest.json` lists every pasted artifact with its sha256.

## A note on the name

`Iceberg_full_repo.zip`'s internal root directory is spelled `Iceburg/`, with
a u. That spelling is preserved in `REPORT.md` as found, and is the likely
origin of the separately-named `wking53214/ICEBURG` repository.
