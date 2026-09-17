# ICEBERG — RAW ARTIFACT RECOVERY

Recovery run 2026-09-16. No code in this package was written, rewritten,
reformatted, corrected, completed, or merged. Every file is a byte-for-byte
copy of what was found. Where raw source was not found, that is stated and
nothing was substituted for it.

## Sources searched

1. Normalized conversation corpus of 65,181 messages built earlier this
   session from six exports — ChatGPT, Claude web, Gemini Apps Activity,
   Copilot, Claude Code local sessions, Codex CLI. Range 2023-09-20 →
   2026-09-16.
2. Full filesystem under `/home/wking53214`.
3. Google Drive mount `/mnt/chromeos/GoogleDrive/MyDrive`.

## Archives

| archive | found | sha256 | entries |
|---|---|---|---|
| `/mnt/chromeos/GoogleDrive/MyDrive/Iceberg_full_repo.zip` | YES | `d96050a9070e6c45722561b65875b0882a0d441c763344f1b329c32ec0b69a72` | 123 |
| `/mnt/chromeos/GoogleDrive/MyDrive/Iceberg_flat.zip` | YES | `0911e85d7aafb985b239e1ac912cc8bf8142996cea054a3fc5442a100f4279cf` | 33 |
| `/home/wking53214/iceberg.zip` | **NOT AN ARCHIVE** — 9 bytes, content is the literal text `Not Found`. A failed download. | — | — |

`Iceberg_full_repo.zip` internal root directory is spelled **`Iceburg/`**
(with a u), not `Iceberg/`. Preserved as found.

Zip entry timestamps: full_repo 2026-07-01 18:53–18:54; flat 2026-07-02 13:54.
Both are LATER than the 2026-06-29 priority window.

## Git repository

No git repository for Iceberg was found. `find` over the filesystem returned
no `Iceberg/.git` or `Iceburg/.git`. One remote branch ref exists in an
unrelated repo — `Gemini_Extraction/.git/refs/remotes/origin/claude/earliest-iceberg-reference-1xtvz9` — which is a branch name only,
containing no Iceberg source.

## Corpus-recovered source artifacts

80 messages in the corpus begin with a `# path.py` header followed by
Python. **Every one is `role: user`** — that is, pasted by the account holder
into Gemini, not generated in the captured record. Each is stored verbatim in
`pasted/` and listed in `pasted_manifest.json` with its sha256.

| time (UTC) | msg id | bytes | sha256 (first 16) | declared path |
|---|---|---:|---|---|
| 2026-06-02T19:19:04 | `g1618-prompt` | 31631 | `213d9792d3a0f1f9` | `observe_full.py` |
| 2026-06-19T23:12:33 | `g1133-prompt` | 5223 | `63e28ee6b9b1d347` | `swarm_sim.py` |
| 2026-06-29T02:33:27 | `g703-prompt` | 1826 | `bde50d9b0c28a961` | `engines/bayes_gpu.py` |
| 2026-06-29T02:34:18 | `g702-prompt` | 4256 | `c80e75cc59ba33e8` | `engines/rl_ppo.py` |
| 2026-06-29T02:35:10 | `g701-prompt` | 3142 | `a84eea58e701166b` | `engines/staffing_rl.py` |
| 2026-06-29T02:36:22 | `g700-prompt` | 4683 | `de3ad493720ad149` | `replay/replay_runner.py` |
| 2026-06-29T02:36:41 | `g699-prompt` | 4477 | `532cd4f744740303` | `replay/verifier.py` |
| 2026-06-29T02:37:04 | `g698-prompt` | 5634 | `79fdb77c4e0ec14d` | `api/server.py` |
| 2026-06-29T02:37:28 | `g697-prompt` | 1546 | `ab7d909ba9816b21` | `api/schemas.py` |
| 2026-06-29T02:37:45 | `g696-prompt` | 5704 | `73b1096565af1073` | `sim/simulator.py` |
| 2026-06-29T02:38:03 | `g695-prompt` | 3109 | `37be593f60d3963c` | `sim/cluster_runner.py` |
| 2026-06-29T02:38:20 | `g694-prompt` | 949 | `176b85a5719f4f7a` | `domain/Intent.py` |
| 2026-06-29T02:39:21 | `g693-prompt` | 958 | `c5d050f2e48c7df0` | `domain/Emotion.py` |
| 2026-06-29T02:40:02 | `g692-prompt` | 1063 | `6da6faccf274e8c2` | `domain/QueueState.py` |
| 2026-06-29T02:40:42 | `g691-prompt` | 4747 | `0b83d4d257cabf26` | `model/build_graph.py` |
| 2026-06-29T02:41:09 | `g690-prompt` | 3170 | `ff59da6ff288cbb9` | `latent/LatentPayload.py` |
| 2026-06-29T02:41:28 | `g689-prompt` | 2885 | `bf39cb32b2755cab` | `telemetry/aggregator.py` |
| 2026-06-29T02:41:45 | `g688-prompt` | 4578 | `8df532cafec665ad` | `engines/rl_ppo.py` |
| 2026-06-29T02:42:17 | `g687-prompt` | 3711 | `79154250a2cad659` | `engines/rl_marl.py` |
| 2026-06-29T02:42:44 | `g686-prompt` | 4132 | `c39ff6b5433faf9d` | `engines/staffing_rl.py` |
| 2026-06-29T02:43:29 | `g685-prompt` | 1703 | `92218d0b87b75e8d` | `replay/recorder.py` |
| 2026-06-29T02:43:51 | `g684-prompt` | 1448 | `696111cfb3833909` | `replay/snapshot.py` |
| 2026-06-29T02:44:07 | `g683-prompt` | 1812 | `49f783b9f79fe58c` | `replay/ledger.py` |
| 2026-06-29T02:44:34 | `g682-prompt` | 6033 | `88faf637f51538fd` | `replay/replay_runner.py` |
| 2026-06-29T02:45:00 | `g681-prompt` | 4492 | `1ef98f72e286bdd1` | `replay/verifier.py` |
| 2026-06-29T02:45:21 | `g680-prompt` | 4396 | `579e22424f6f7335` | `simulator/simulator.py` |
| 2026-06-29T02:45:46 | `g679-prompt` | 3356 | `568660ce99296986` | `simulator/cluster_runner.py` |
| 2026-06-29T02:46:03 | `g678-prompt` | 2351 | `20b77c7b7d4200be` | `main.py` |
| 2026-06-29T02:46:37 | `g677-prompt` | 2370 | `f5d192331f9df306` | `config.py` |
| 2026-06-29T02:47:18 | `g675-prompt` | 3549 | `01676e2f7bc89e17` | `governance/governance.py` |
| 2026-06-29T02:47:59 | `g673-prompt` | 3615 | `298ea840b4d289e2` | `api/http_api.py` |
| 2026-06-29T02:48:26 | `g672-prompt` | 4359 | `d77df27a5c703b13` | `cli.py` |
| 2026-06-29T02:48:49 | `g671-prompt` | 3568 | `631c5e426be300bf` | `model/build_graph.py` |
| 2026-06-29T02:49:14 | `g670-prompt` | 1787 | `4377dc96deadd843` | `domain/CallerState.py` |
| 2026-06-29T02:49:31 | `g669-prompt` | 976 | `5d5f4f538fbf3a0c` | `domain/Intent.py` |
| 2026-06-29T02:49:52 | `g668-prompt` | 993 | `852214162419300e` | `domain/Emotion.py` |
| 2026-06-29T02:50:09 | `g667-prompt` | 1102 | `84e9bda508b291ce` | `domain/QueueState.py` |
| 2026-06-29T02:50:27 | `g666-prompt` | 2267 | `5b3136217507dafc` | `latent/LatentPayload.py` |
| 2026-06-29T02:51:09 | `g665-prompt` | 4499 | `4eb842d3406c722d` | `engines/rl_ppo.py` |
| 2026-06-29T02:51:30 | `g664-prompt` | 3733 | `afdf567808853ab0` | `engines/rl_marl.py` |
| 2026-06-29T02:52:13 | `g663-prompt` | 4101 | `936d6dd9c498d751` | `engines/staffing_rl.py` |
| 2026-06-29T02:52:39 | `g662-prompt` | 5740 | `788577081649faa4` | `simulator/simulator.py` |
| 2026-06-29T02:53:16 | `g661-prompt` | 2485 | `171f7254186f67e6` | `replay/ReplayRecorder.py` |
| 2026-06-29T02:53:37 | `g660-prompt` | 5068 | `e91e877e34d543f1` | `replay/ReplayVerifier.py` |
| 2026-06-29T02:54:04 | `g659-prompt` | 4832 | `571f1f35bb9ac600` | `replay/SnapshotManager.py` |
| 2026-06-29T03:02:36 | `g658-prompt` | 4455 | `47d17c9eb6f16283` | `replay/ReplayRunner.py` |
| 2026-06-29T03:03:01 | `g657-prompt` | 4166 | `61b48699b2c80e3c` | `cli/iceberg_cli.py` |
| 2026-06-29T03:03:28 | `g656-prompt` | 2935 | `6f03a84f05e9cac8` | `telemetry/TelemetryAggregator.py` |
| 2026-06-29T03:04:00 | `g655-prompt` | 3901 | `cc5e2374ff2324dc` | `cluster/ClusterRunner.py` |
| 2026-06-29T03:06:09 | `g654-prompt` | 4715 | `c7300f698dd042e2` | `governance/GovernanceEnvelope.py` |
| 2026-06-29T03:06:43 | `g653-prompt` | 5809 | `5c11f5e3112fe550` | `api/http_api.py` |
| 2026-06-29T03:07:19 | `g652-prompt` | 3806 | `2840478b79a32f4f` | `dashboard/DashboardServer.py` |
| 2026-06-29T03:07:47 | `g651-prompt` | 6397 | `21058b5b0282d6e0` | `admin/AdminConsole.py` |
| 2026-06-29T03:09:09 | `g650-prompt` | 5756 | `daf62ca3ca4d575e` | `extraction/ExtractionOS.py` |
| 2026-06-29T04:08:21 | `g648-prompt` | 5756 | `daf62ca3ca4d575e` | `extraction/ExtractionOS.py` |
| 2026-06-29T04:09:11 | `g645-prompt` | 5286 | `b17506161831204f` | `extraction/ManifestValidator.py` |
| 2026-06-29T04:10:36 | `g643-prompt` | 4841 | `8bef226814a2fbec` | `extraction/ExtractionOS_Driver.py` |
| 2026-06-29T04:12:14 | `g642-prompt` | 3188 | `dd0f436df620cd85` | `extraction/BackwardsDrain.py` |
| 2026-06-29T04:13:29 | `g640-prompt` | 3331 | `3228e4028c6d5d42` | `extraction/ForwardDrain.py` |
| 2026-06-29T04:14:07 | `g637-prompt` | 2722 | `452feaebb1e87ec0` | `policy/PolicyMarketplace.py` |
| 2026-06-29T04:15:04 | `g635-prompt` | 949 | `176b85a5719f4f7a` | `domain/Intent.py` |
| 2026-06-29T04:15:41 | `g633-prompt` | 958 | `c5d050f2e48c7df0` | `domain/Emotion.py` |
| 2026-06-29T04:16:20 | `g631-prompt` | 3439 | `5a87de1bb6da7f62` | `graph/GraphModel.py` |
| 2026-06-29T04:17:16 | `g629-prompt` | 3164 | `4e73f54b3126f149` | `graph/GraphBuilder.py` |
| 2026-06-29T04:18:12 | `g628-prompt` | 3185 | `35f68b94c894e852` | `graph/GraphBuilder.py` |
| 2026-06-29T04:19:03 | `g626-prompt` | 3912 | `697c8e4d01720384` | `graph/GraphPresets.py` |
| 2026-06-29T04:21:00 | `g624-prompt` | 2238 | `a76e39de80fb3294` | `graph/NodeModel.py` |
| 2026-06-29T04:22:57 | `g622-prompt` | 4525 | `b39b531a9fc49f33` | `load/LoadTester.py` |
| 2026-06-29T04:23:53 | `g620-prompt` | 4637 | `fc4fbb177127be95` | `policy/PolicyExamples.py` |
| 2026-06-29T04:25:13 | `g618-prompt` | 4021 | `7554af5e3ba9dfeb` | `graph/NodeRoutingRules.py` |
| 2026-06-29T04:26:27 | `g616-prompt` | 4032 | `227dc8e514b2e7a9` | `graph/GraphAnalytics.py` |
| 2026-06-29T04:27:32 | `g614-prompt` | 4217 | `c90e60e45333b71f` | `admin/IcebergAdminDashboard.py` |
| 2026-06-29T04:29:16 | `g612-prompt` | 2823 | `090d51f2e9a8fe4e` | `admin/DashboardServer.py` |
| 2026-06-29T04:30:12 | `g610-prompt` | 3834 | `1cfec343cb2f9621` | `graph/RoutingDiagnostics.py` |
| 2026-06-29T04:31:12 | `g608-prompt` | 5129 | `332c61a791dc37b0` | `rl/MARLTrainer.py` |
| 2026-06-29T04:32:13 | `g606-prompt` | 4186 | `feee51b75cc0c284` | `rl/PPOTrainer.py` |
| 2026-06-29T04:33:19 | `g604-prompt` | 4261 | `48f6c6366d61d0d4` | `rl/AgentModel.py` |
| 2026-06-29T04:34:41 | `g602-prompt` | 4030 | `9587d06012ae0253` | `telemetry/Telemetry.py` |
| 2026-06-29T04:35:53 | `g600-prompt` | 5486 | `93de47656ca75eca` | `governance/GovernanceEnvelope.py` |
| 2026-06-29T04:37:11 | `g598-prompt` | 3189 | `f905e8b6f68ebf62` | `replay/ReplayRunner.py` |

### Provenance note on all of the above

Source: Gemini Apps **Activity** export. That export has no canonical speaker
field; the normalizer labels the `Prompted …` half `user` and the rendered
half `UNKNOWN`. The `user` label on these rows is therefore structural — the
text sat in the prompt half of the activity record. The paired model
responses for these messages are prose acknowledgements ("The source code for
X has been tracked"), not code.

## PRIORITY TARGET STATUS

| # | target | status | where |
|---|---|---|---|
| 1 | `ICEBERG_RUNTIME_CONTROLLER` | **RAW SOURCE NOT RECOVERED** | Only the request exists: `g439-prompt`, 2026-06-30T01:25:34Z, 53 bytes, full text `Provide me the content for ICEBERG_RUNTIME_CONTROLLER`. No response row captured. |
| 2 | `ICEBERG_KERNEL_ADAPTER_REGISTRY` | **RAW SOURCE NOT RECOVERED** | Only the request: `g438-prompt`, 2026-06-30T01:30:46Z, 55 bytes. No response captured. (`Iceburg/Registry/module_registry.py` exists in the zip; whether it is the same artifact is NOT asserted here.) |
| 3 | `ICEBERG_RL_ENGINES_DEV` | **RAW SOURCE NOT RECOVERED** | Only the request: `g436-prompt`, 2026-06-30T01:36:11Z, 46 bytes. No response captured. |
| 4 | `CallerState` | RAW SOURCE RECOVERED | `g670-prompt` 2026-06-29T02:49:14Z; also `Iceburg/Domain/CallerState.py`, `flat/CallerState.py` |
| 5 | `DynamicState` | RAW SOURCE RECOVERED | Defined inside CallerState.py — `pasted/…g670…` line 11; zip copies line 23 |
| 6 | `LatentPayload` | RAW SOURCE RECOVERED (2 corpus versions) | `g690-prompt` 02:41:09Z, `g666-prompt` 02:50:27Z; zip `Iceburg/Latent/LatentPayload.py`, `flat/LatentPayload.py` |
| 7 | `QueueState` | RAW SOURCE RECOVERED (2 corpus versions) | `g692-prompt` 02:40:02Z, `g667-prompt` 02:50:09Z; zip copies |
| 8 | `IcebergSimulator` | RAW SOURCE RECOVERED (3 distinct corpus versions) | `g696-prompt` 02:37:45Z, `g680-prompt` 02:45:21Z, `g662-prompt` 02:52:39Z — all differ |
| 9 | `simulator.py` | RAW SOURCE RECOVERED | as above; plus `Iceburg/Sim/Simulator.py`, `flat/Simulator.py` |
| 10 | `replay/recorder.py` | RAW SOURCE RECOVERED | `g685-prompt` 02:43:29Z; zip `Iceburg/Replay/recorder.py` |
| 11 | `replay/snapshot.py` | RAW SOURCE RECOVERED | `g684-prompt` 02:43:51Z; zip `Iceburg/Replay/snapshot.py` |
| 12 | `replay/ledger.py` | RAW SOURCE RECOVERED | `g683-prompt` 02:44:07Z; zip `Iceburg/Replay/ledger.py` |
| 13 | `replay/replay_runner.py` | RAW SOURCE RECOVERED (2 corpus versions) | `g700-prompt` 02:36:22Z, `g682-prompt` 02:44:34Z; zip copy |
| 14 | `replay/verifier.py` | RAW SOURCE RECOVERED (2 corpus versions) | `g699-prompt` 02:36:41Z, `g681-prompt` 02:45:00Z; zip copy |
| 15 | `engines/rl_ppo.py` | RAW SOURCE RECOVERED (3 corpus versions) | `g702` 02:34:18Z, `g688` 02:41:45Z, `g665` 02:51:09Z; zip copy |
| 16 | `engines/rl_marl.py` | RAW SOURCE RECOVERED (2 corpus versions) | `g687` 02:42:17Z, `g664` 02:51:30Z; zip copy |
| 17 | `engines/staffing_rl.py` | RAW SOURCE RECOVERED (3 corpus versions) | `g701` 02:35:10Z, `g686` 02:42:44Z, `g663` 02:52:13Z; zip copy |
| 18 | `engines/bayes_gpu.py` | RAW SOURCE RECOVERED | `g703-prompt` 02:33:27Z; zip `Iceburg/Engines/bayes_gpu.py`, `flat/bayes_gpu.py` |
| 19 | `domain/Intent.py` | RAW SOURCE RECOVERED (3 corpus versions) | `g694` 02:38:20Z, `g669` 02:49:31Z, `g635` 04:15:04Z; zip copy |
| 20 | `domain/Emotion.py` | RAW SOURCE RECOVERED (3 corpus versions) | `g693` 02:39:21Z, `g668` 02:49:52Z, `g633` 04:15:41Z; zip copy |
| 21 | `model/build_graph.py` | RAW SOURCE RECOVERED (2 corpus versions) | `g691` 02:40:42Z, `g671` 02:48:49Z; zip `Iceburg/Model/Build_Graph.py` |
| 22 | `telemetry/aggregator.py` | RAW SOURCE RECOVERED | `g689-prompt` 02:41:28Z; zip `Iceburg/Telemetry/aggregator.py` |
| 23 | `GsaUniversalAdapter` | RAW SOURCE RECOVERED — **OUTSIDE PRIORITY WINDOW** | Earliest class definition 2026-07-04T19:33:44Z (`g230-response`). 234 corpus messages contain a definition. Also on disk in `sentinel_os/sage_k/`, `ANVIL/ANVIL.py`, `Downloads/GSA_MAGNA_CORE_v11_HARDENED.py`. Samples in `gsa_adapter/`. |
| 24 | `GsaTemporalDoorwayGate` | RAW SOURCE RECOVERED — **OUTSIDE PRIORITY WINDOW** | Same conversations and files as #23; 192 corpus messages mention it. |

## The scaffold you cited

Recovered verbatim as `corpus_artifacts/20260629T023229_g704-prompt.txt`.

- **Recorded time: 2026-06-29T02:32:29.606Z (UTC).** You cited 12:52 PM. The
  record does not carry a 12:52 timestamp for this content; the discrepancy is
  reported, not resolved.
- Re-pasted identically in content at 2026-06-29T04:51:57.426Z (`g576-prompt`),
  different sha256 only because of a leading-space difference.
- The tree matches the one you described, including `certification/`,
  `website/`, `marketing/`, `training/modules/`, `deploy/k8s/`.
- It is a **request**: the message opens `an you help me build this zip file
  if I give you the code snippets?` — the pastes in the table above are the
  snippets that followed it over the next ~2 hours.

## The 07:20 AM artifact you cited

At **2026-06-29T11:20:35.018Z (07:20 EDT)** the record shows:

- `g567-prompt` (user, 83 bytes): `No, the code for Simulator.py for Iceburg
  with code function description at the top`
- `g567-response`: prose describing **a literal iceberg physics simulation** —
  "models iceberg melting and buoyancy dynamics … Archimedes' principle"
- `g566-title` at 11:20:39Z: `Created Gemini Canvas titled Iceberg Buoyancy and
  Melting Simulator`

**DESCRIPTION ONLY — RAW SOURCE NOT RECOVERED.** Gemini Canvas contents are
not carried in the Activity export. No `class IcebergSimulator` appears at this
timestamp in any corpus; the three occurrences of that class are at 02:37:45Z,
02:45:21Z and 02:52:39Z. Whether the uncaptured canvas contained it cannot be
determined from the available record.

## PARTIAL RAW SOURCE — image-derived

At 2026-06-29T17:31–17:35Z, code was supplied as photographs (`IMG_4138.jpg` –
`IMG_4148.jpg`), followed by `Give me the consolidated code from all the images`
(`g520-prompt`, 17:33:11Z). The next message `g519-prompt` (17:33:40Z, 13,542
bytes) carries text with run-together tokens characteristic of image text
extraction — e.g. `import argparseimport csvimport jsonimport logging`.

Preserved exactly as found in `corpus_artifacts/20260629T173340_g519-prompt.txt`.
**Not corrected.** The images themselves are not in the corpus.

## Other Iceberg files on disk (all post-date the priority window)

| path | mtime | bytes |
|---|---|---|
| `ARCHIVE__extracted__report_9__IcebergProductionHarness.py` | 2026-08-19 09:59:38.181996 | 7767 |
| `GSA-815__iceberg_complete_simulator.py` | 2026-08-28 11:24:46.589675 | 8085 |
| `OBSERVE__sentinel_os__iceberg_complete_simulator.py` | 2026-09-02 17:01:44.317635 | 7717 |
| `TAKEOUT__Takeout__My Activity__Gemini Apps__iceberg_session_handoff_v1.txt` | 2026-07-09 07:02:42 | 9074 |

## Explicit answers to the checklist

- **Original ICEBERG repository/archive:** two archives found on Google Drive (above). No source repository as such.
- **Iceberg_full_repo.zip:** FOUND — `/mnt/chromeos/GoogleDrive/MyDrive/`, 101,418 bytes, 123 entries, extracted to `full_repo/`.
- **Iceberg_flat.zip:** FOUND — same directory, 66,403 bytes, 33 entries, extracted to `flat/`.
- **Original Git repository:** NOT FOUND.
- **Generated .py files:** none in the captured record. Every corpus source artifact is a user paste; the model's captured replies are prose.
- **Attached Python files:** one referenced but not captured — a ChatGPT message at 2026-06-28T21:35:32Z says "you've uploaded a Python implementation of your Latent Iceberg Model v1.2.0". The upload itself is not in the export. DESCRIPTION ONLY.
- **Code blocks copied from an earlier Iceberg version:** yes — the 2026-06-28 ChatGPT thread references "Latent Iceberg Model v1.2.0" and Iceberg "2.0", while the 2026-06-29 pastes are headed "Iceberg 3.x". Earlier-version raw source was NOT recovered.

## Not recovered — stated plainly

- ICEBERG_RUNTIME_CONTROLLER — **RAW SOURCE NOT RECOVERED**
- ICEBERG_KERNEL_ADAPTER_REGISTRY — **RAW SOURCE NOT RECOVERED**
- ICEBERG_RL_ENGINES_DEV — **RAW SOURCE NOT RECOVERED**
- The 2026-06-29 07:20 canvas — **DESCRIPTION ONLY — RAW SOURCE NOT RECOVERED**
- Latent Iceberg Model v1.2.0 / Iceberg 2.0 — **DESCRIPTION ONLY — RAW SOURCE NOT RECOVERED**
- IMG_4138–4148.jpg originals — **NOT RECOVERED** (only the extracted text)

No replacement code was generated for any of the above.
