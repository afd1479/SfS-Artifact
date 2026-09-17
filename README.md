# Shuffling for Safeguarding (SfS) Artifact

This repository contains the research artifact for:

> Ala Darabseh and Christina Pöpper, “Shuffling for Safeguarding (SfS):
> Replay Protection in Wireless Broadcast Systems,” ACSAC 2026.

The artifact provides two complementary evaluation paths:

1. **Offline result reproduction:** regenerate the numerical tables and plots
   for paper Figures 3--11 from the supplied packet-level Excel workbooks.
   This path requires no special hardware.
2. **Live prototype evaluation:** run the parameterized SfS sender, receiver,
   ordinary-replay attacker, permutation-aware attacker, and performance
   programs on a controlled Raspberry Pi wireless testbed.

## Artifact links

- Source repository: <https://github.com/afd1479/SfS-Artifact>
- Reserved archival DOI: <https://doi.org/10.5281/zenodo.22801028>

The Zenodo DOI has been reserved so it can be embedded in the artifact. It will
resolve after the final Zenodo record is published.

## Evaluation paths

| Path | Purpose | Requirements | Starting point |
|---|---|---|---|
| Offline reproduction | Reproduce Figures 3--11 and their numerical CSV inputs | Standard workstation, Python 3; no GPU | [Quick start](#quick-start-offline-reproduction) |
| Scaled live evaluation | Exercise all testbed roles with four 100-packet runs | Three Raspberry Pis and an isolated 2.4 GHz IBSS/ad-hoc network | [`SCALED_EVALUATION.md`](SfS_RaspberryPi_Testbed_v1.0/docs/SCALED_EVALUATION.md) |
| Full live experiments | Collect new legitimate, replay, and performance workbooks | Same three-device testbed | [`RUN_EXPERIMENTS.md`](SfS_RaspberryPi_Testbed_v1.0/docs/RUN_EXPERIMENTS.md) |

The deterministic paper-result check is the offline path. Fresh wireless runs
exercise the implementation, but their timestamps, delivery counts, and
performance values are expected to depend on the evaluator's environment.

## Repository layout

```text
SfS-Artifact/
├── README.md
├── LICENSE                         # MIT license for source code
├── LICENSE-DATA                    # CC BY 4.0 license for data and documentation
├── CITATION.cff
├── install.sh
├── claims/                         # Claim-to-artifact mapping and entry points
├── SfS_Artifact_Reproduction/      # Raw workbooks and Figure 3--11 reproduction
└── SfS_RaspberryPi_Testbed_v1.0/   # Parameterized three-Pi implementation
```

The two package directories retain their own detailed README files.

## Quick start: offline reproduction

From a clone of the repository:

```bash
git clone https://github.com/afd1479/SfS-Artifact.git
cd SfS-Artifact
bash install.sh analysis
bash claims/claim1_figures_3_11/run.sh
```

The installation script creates `.venv-analysis` and installs the packages
listed in `SfS_Artifact_Reproduction/requirements.txt`. The claim runner invokes
`SfS_Artifact_Reproduction/reproduce_all.py` from the correct directory.

Expected outputs are:

- PDF and PNG plots under `SfS_Artifact_Reproduction/figures/`;
- numerical CSV inputs under `SfS_Artifact_Reproduction/derived/`; and
- `SfS_Artifact_Reproduction/derived/validation_report.csv`.

Use `SfS_Artifact_Reproduction/PLOT_MAPPING.md` to map each generated file to
its paper figure. Minor visual differences across Matplotlib versions are
acceptable; the derived counts and rates are the primary validation evidence.

To install both the offline and testbed Python dependencies, run:

```bash
bash install.sh all
```

`install.sh` installs Python packages only. Raspberry Pi operating-system
packages, Chrony, and the IBSS/ad-hoc network require the manual system setup in
[`RASPBERRY_PI_SETUP.md`](SfS_RaspberryPi_Testbed_v1.0/docs/RASPBERRY_PI_SETUP.md).

## Claims and expected evidence

The [`claims/`](claims/README.md) directory is the authoritative claim map.

| Claim | Paper evidence | Hardware-free validation | Optional live validation |
|---|---|---|---|
| [Figures 3--11](claims/claim1_figures_3_11/README.md) | Detection results across legitimate, ordinary-replay, and permutation-aware cases | Reproduce all figures and derived CSV files | Not required |
| [Legitimate and ordinary replay](claims/claim2_ordinary_replay/README.md) | No-attack and ordinary-replay evaluation underlying Figures 3--10 | Inspect and regenerate the supplied results | Scaled Runs B and C |
| [Permutation-aware replay](claims/claim3_permutation_aware_replay/README.md) | Figure 11 | Inspect and regenerate the supplied result | Scaled Run D |
| [Prototype performance](claims/claim4_performance/README.md) | Signing, verification, throughput, and latency measurements | Inspect the documentation and supplied evidence | Scaled Run A |

## Raspberry Pi testbed

The live setup uses three devices:

| Device | Role | Default address | Programs |
|---|---|---:|---|
| Raspberry Pi 1 | Sender | `192.168.1.11` | `sender.py`, `sender_throughput.py` |
| Raspberry Pi 2 | Receiver | `192.168.1.12` | `receiver.py`, `receiver_throughput.py` |
| Raspberry Pi 3 | Attacker | `192.168.1.10` | `ordinary_replay_attacker.py`, `smart_replay_attacker.py` |

All three devices use UDP port `5005` on an isolated 2.4 GHz IBSS/ad-hoc
network and synchronize their system clocks with Chrony. Start the receiver
first, the selected attacker second, and the sender last. Do not run both
attacker programs simultaneously.

Review these documents before a live run:

1. [`RASPBERRY_PI_SETUP.md`](SfS_RaspberryPi_Testbed_v1.0/docs/RASPBERRY_PI_SETUP.md)
2. [`PARAMETERS.md`](SfS_RaspberryPi_Testbed_v1.0/docs/PARAMETERS.md)
3. [`SCALED_EVALUATION.md`](SfS_RaspberryPi_Testbed_v1.0/docs/SCALED_EVALUATION.md)
4. [`RUN_EXPERIMENTS.md`](SfS_RaspberryPi_Testbed_v1.0/docs/RUN_EXPERIMENTS.md)
5. [`OUTPUTS_AND_PERFORMANCE.md`](SfS_RaspberryPi_Testbed_v1.0/docs/OUTPUTS_AND_PERFORMANCE.md)

The scaled procedure uses four 100-packet runs and normally takes about 15--30
minutes after the network and devices are configured. The complete experiment
matrix takes longer and depends on the selected parameters and testbed.

### Coordinates and delay calibration

The laboratory did not use live GPS/GNSS devices. Sender and receiver
coordinates are therefore retained as experimental metadata rather than live
position measurements. In the supplied implementation, the active receiver
estimate uses a calibrated mean end-to-end delay; changing only the coordinates
does not change verification timing.

The authors measured a mean delay of `0.29` seconds on their laboratory
testbed. This value includes the behavior of that complete test environment and
is not a universal physical propagation time. Evaluators must run the local
calibration in Scaled Run A and pass the resulting value with
`--mean-delay-s` for their own hardware and network. A deployment with a
GPS/GNSS source may populate accurate live coordinates, but any
coordinate-derived timing method must be implemented and validated
consistently at the receiver.

## Output and overwrite behavior

- Offline reproduction overwrites generated content in
  `SfS_Artifact_Reproduction/figures/` and
  `SfS_Artifact_Reproduction/derived/`. It does not modify the raw workbooks in
  `SfS_Artifact_Reproduction/data/`.
- Sender and receiver programs may overwrite an existing workbook when the same
  `--output` path is reused. Use a distinct output name for every live run.
- The programs use UDP, so a live receiver may record fewer packets than were
  sent. Packet loss and environment-dependent timing are not failures by
  themselves.

## Data provenance

The released `.xlsx` workbooks contain packet-level records generated on the
authors' controlled wireless testbed at New York University Abu Dhabi between 
approximately March 2025 and April 2026. The experiments used separate Raspberry 
Pi sender, receiver, and attacker roles, an isolated 2.4 GHz IBSS/ad-hoc network,
and Chrony clock synchronization. The directory structure records experiment type,
THV, and replay delay. The raw workbooks under `SfS_Artifact_Reproduction/data/` 
are the inputs for the provided analysis; the `derived/` tables and `figures/` 
outputs can be regenerated from them.

The parameterized testbed package preserves the evaluated experiment flow and
exposes the principal settings as command-line options for inspection,
extension, and new validation runs. New live measurements may differ slightly
from the supplied workbooks because of hardware, operating-system scheduling,
storage, synchronization, and wireless conditions.

**Release blocker:** before the final public release, the authors must replace
this sentence with the actual start and end dates of the original workbook
collection. The available records do not establish those dates reliably, so
they have not been guessed here.

## Data ethics and privacy

The artifact contains records generated by a controlled wireless research
testbed. It does not contain human-subject data, personal data, user traffic,
or credentials collected from a production network. Packet identifiers,
timestamps, classifications, and performance measurements describe the
experiment itself. The artifact must not be used to capture or replay traffic
on networks for which the evaluator lacks authorization.

## Security and safety notice

The prototype uses Python `pickle` serialization and includes experimental RSA
key material in the source. Unpickling untrusted network data can execute
malicious code. Run the testbed programs only on a controlled, isolated
research network with trusted devices. The included key material,
serialization format, and default addressing are not suitable for production
deployment.

## Citation

Until the archival record and paper proceedings are published, cite the paper
as follows:

```bibtex
@inproceedings{darabseh2026sfs,
  author    = {Ala Darabseh and Christina P{\"o}pper},
  title     = {Shuffling for Safeguarding (SfS): Replay Protection in Wireless Broadcast Systems},
  booktitle = {Annual Computer Security Applications Conference (ACSAC)},
  year      = {2026}
}
```

The root [`CITATION.cff`](CITATION.cff) also provides machine-readable citation
metadata. After the final Zenodo publication, the reserved DOI above is the
preferred citation for the artifact itself.

## License

This is a mixed research artifact with separate licenses:

- Source code, scripts, and software configuration files are licensed under
  the **MIT License**. See [`LICENSE`](LICENSE).
- Experimental datasets, generated data tables, figures, and documentation are
  licensed under the **Creative Commons Attribution 4.0 International License
  (CC BY 4.0)**. See [`LICENSE-DATA`](LICENSE-DATA).

Unless a file states otherwise, `.py` and `.sh` files fall under MIT, while
`.xlsx`, `.csv`, `.png`, `.pdf`, and `.md` artifact files fall under CC BY 4.0.
The conference paper, third-party dependencies, external trademarks, and any
third-party material retain their own terms and are not relicensed by this
repository.

Copyright (c) 2026 Ala Darabseh and Christina Pöpper.

