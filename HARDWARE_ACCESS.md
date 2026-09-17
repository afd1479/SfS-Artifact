# Hardware Requirements and Access Policy

## Access status

The SfS artifact does **not** provide an author-hosted, always-on SSH service or
remote access to the authors' Raspberry Pi devices. No private cloud, API key,
account, VPN credential, or other restricted service is required for the
primary offline evaluation.

All source code, raw experimental workbooks, analysis programs, claim mappings,
and setup documentation will be released through the public GitHub repository
and the permanent Zenodo record.

## Why remote hardware access is not provided

The live experiment is a coordinated physical wireless testbed rather than a
single machine that can be exposed safely as a remote build server. It requires:

- three Raspberry Pi devices running sender, receiver, and attacker roles;
- a dedicated 2.4 GHz wireless interface on each device in IBSS/ad-hoc mode;
- static placement and controlled wireless conditions;
- Chrony synchronization across the devices;
- receiver, attacker, and sender processes started in the documented order;
- manual observation and shutdown so that final workbooks are saved; and
- physical recovery if a wireless interface, process, or device becomes
  unreachable.

SSH by itself is not expected to exhaust a Raspberry Pi. The limiting issues
are maintaining reliable and secure Internet access to all three devices,
separating management traffic from the experimental wireless network,
coordinating concurrent processes, recovering failed devices, and avoiding
changes to the timing and throughput measurements caused by remote-management
activity. The authors therefore cannot guarantee a stable, evaluator-operated
remote testbed throughout the artifact-evaluation period.

## Evaluation paths

### 1. Primary path: offline reproduction

Evaluators can reproduce the numerical inputs and plots for paper Figures
3--11 on a standard workstation without Raspberry Pi hardware:

```bash
bash install.sh analysis
bash claims/claim1_figures_3_11/run.sh
```

The command reads the released packet-level workbooks and regenerates the
derived CSV files plus PDF and PNG figures. The expected evidence and accepted
tolerance are documented in
[`claims/claim1_figures_3_11/README.md`](claims/claim1_figures_3_11/README.md).

### 2. Optional path: scaled live evaluation

Evaluators who have suitable hardware can exercise every live code path using
the four 100-packet runs in
[`SfS_RaspberryPi_Testbed_v1.0/docs/SCALED_EVALUATION.md`](SfS_RaspberryPi_Testbed_v1.0/docs/SCALED_EVALUATION.md).
After the devices have been configured, the four runs normally take about
15--30 minutes. They cover delay calibration, legitimate traffic, ordinary
replay, permutation-aware replay, and performance instrumentation.

The scaled run is a functional execution check. It is not expected to reproduce
the complete paper statistics from a 100-packet wireless sample.

### 3. Full fresh collection

Researchers may collect new full-size workbooks by following
[`SfS_RaspberryPi_Testbed_v1.0/docs/RUN_EXPERIMENTS.md`](SfS_RaspberryPi_Testbed_v1.0/docs/RUN_EXPERIMENTS.md).
Results from a newly constructed testbed are expected to vary with device
model, operating system, CPU load, storage, placement, interference, packet
loss, and clock synchronization.

## Required hardware for a live run

| Quantity | Component | Requirement |
|---:|---|---|
| 3 | Raspberry Pi devices | One sender, one receiver, and one attacker |
| 3 | 2.4 GHz Wi-Fi interfaces | Driver must support IBSS/ad-hoc mode |
| 3 | Power supplies and microSD cards | Suitable for the selected Pi models |
| 1 | Isolated test area | Static line of sight; the authors used approximately 3--5 m separation |
| 3 | Local consoles or management connections | Needed for setup, process control, and recovery |

The default testbed addresses are sender `192.168.1.11`, receiver
`192.168.1.12`, and attacker `192.168.1.10`, using UDP port `5005`. These values
are configurable in the supplied programs and are not assumptions that require
the evaluator to reproduce the authors' exact laboratory network.

## Calibration requirement

The active receiver estimate uses a measured mean end-to-end delay. The
authors' laboratory value was `0.29` seconds, but it is not universal and must
not be treated as the physical propagation time for another deployment.
Evaluators performing a live run must execute Scaled Run A and pass their own
calibrated value with `--mean-delay-s`.

The source includes sender and receiver coordinates as configurable metadata.
The authors' laboratory did not use live GPS/GNSS devices, and changing only
those coordinates does not change verification timing in the current
implementation.

## Artifact-evaluation scope

The [ACSAC 2026 artifact instructions](https://www.acsac.org/2026/submissions/papers/artifacts/)
expect public infrastructure when feasible and recognize exceptions for special
hardware, with anonymous remote access requested when feasible. This artifact
uses that special-hardware exception and documents why an author-hosted remote
testbed is not operationally feasible.

The artifact asks evaluators to use the hardware-free Figure 3--11 procedure as
the primary reproducibility task. The live Raspberry Pi procedures are fully
documented and source-complete, but remote author-hosted hardware is not part of
the submitted or publicly released artifact.

If the Artifact Evaluation Committee determines that direct access to the
authors' physical devices is essential, the authors request that the committee
contact them through the official artifact-review channel so that feasibility
and an evaluation-safe arrangement can be discussed. Any alternative must
preserve evaluator anonymity, testbed security, and measurement integrity; it
must not be assumed available unless the committee and authors agree to it.

## Support during evaluation

At least one knowledgeable author will monitor the official artifact-review
channel during the evaluation period and respond to installation, execution,
and interpretation questions. The repository does not include analytics,
tracking code, or mechanisms intended to identify evaluators.
