  # Edge-Assisted Smart Home Gateway with Hardware-Level Air-Gap

  > A Deterministic Physical Isolation Architecture for Edge Computing — From Patent Concept to Hardware Prototype and Academic Validation

  ---

  ## Project Background

  The proliferation of cloud-centric smart home ecosystems has introduced a fundamental privacy contradiction: sensitive acoustic data is continuously streamed to third-party servers for semantic parsing, exposing users to unauthorized eavesdropping, side-channel exfiltration, and service disruption. Conventional mitigations — software-defined firewalls, VLAN-based logical isolation, or even Trusted Execution Environments (TEEs) — remain probabilistic in nature. They share the same underlying silicon and execution environment as the untrusted OS, and are therefore inherently vulnerable to zero-day exploits and side-channel attacks (see paper Section II for a review of TrustZone/SGX side-channel literature).

  Applying first-principles reasoning: if the goal is *absolute* privacy rather than *probabilistically low-risk* privacy, isolation must be enforced at the physical layer, not the logical layer. This project explores that idea through a hardware-level air-gap mechanism — physically severing the WAN power domain via a relay/MOSFET, rather than relying on software to "promise" isolation.

  ---

  ## Core Achievements

  | Item | Detail |
  |---|---|
  | **Patent** | *A Smart Central Control System and Method Based on Physical Fusing Mechanism* — Application No. 202610261302.7, currently under substantive examination. Sole applicant and first inventor. |
  | **Paper** | Y. Chen and M. Zha, *"Edge-Assisted Smart Home Gateway with Hardware-Level Air-Gap for Deterministic Privacy,"* IEEE GAIIS 2026 (first author). |
  | **Prototype** | Dual-path communication topology (Wi-Fi WAN / Zigbee LAN) + electromagnetic relay physical fusing module, running on Raspberry Pi. |

  ---

  ## ⚠️ Hardware Note (Important — Please Read Before Reviewing Data)

  The published paper text (Section V-A) describes the edge computing node as a **Raspberry Pi 4B**. This reflects the architecture as designed during the early theoretical validation phase.

  The **actual hardware prototype shown in Fig. 3, and the latency data reported in Fig. 4 (0.002–0.056 ms), were measured on a Raspberry Pi 5**, after the hardware was iterated for higher computational headroom. This discrepancy between the paper text and the actual test hardware is disclosed here for full transparency. The core algorithmic logic (rule-based NLU parsing) and the resulting latency order-of-magnitude are consistent across both Pi 4B and Pi 5.

  Note: The two other latency figures reported in the paper abstract — WAN power-domain physical disconnection (≤ 5 ms) and full end-to-end actuation (≤ 30 ms) — are distinct, higher-level system metrics and are not in conflict with the sub-millisecond NLU parsing latency (0.002–0.056 ms) discussed above and in the benchmark section below.

  ---

  ## Technical Evolution — Route 1 (Main Line → Patent & Paper)

  This route represents the technical path that directly produced the patented architecture and the published paper. **It does not involve any LLM component** — the NLU module is a lightweight, deterministic keyword/rule-matching engine, chosen specifically because it guarantees sub-millisecond, reproducible latency, which an LLM-based approach cannot offer at this hardware scale.

  1. Hardware-level air-gap mechanism design (relay/MOSFET on WAN power rail).
  2. Dual-path heterogeneous topology (WAN/LAN physical + logical decoupling).
  3. Offline, rule-based NLU pipeline for local device control (lighting, HVAC, scene switching).
  4. Empirical validation on Raspberry Pi 4B (theoretical stage) → Raspberry Pi 5 (final prototype and data collection).

  See `jarvis_main.py` (core control logic) and `voice_engine.py` (offline speech recognition) for implementation details.

  ---

  ## Latency Benchmark — Two Measurement Conditions

  This repository provides two separate benchmark scripts, measuring **different things**. Please do not conflate their results:

  | Script | What it measures | Environment | Expected order of magnitude |
  |---|---|---|---|
  | `benchmark/jarvis_nlu_pure_benchmark.py` | Pure NLU parsing function only (`ask_jarvis_brain_edge`), single-threaded | Any machine, no GPIO/MQTT/Flask/voice-thread interference | ~0.01 ms (median), matching the paper's reported range under low background noise |
  | `benchmark/benchmark_full_system.py` | Full end-to-end system under real concurrent load | Raspberry Pi, with GPIO + MQTT + Flask + voice-listening threads running | Higher and less stable, reflecting real deployment overhead |

  The demo video (`prototype/demo_video_route1.mp4`) shows multiple consecutive NLU latency measurements captured live in the terminal during operation. Due to the camera angle and terminal scrolling during recording, not every measurement is fully legible on screen, but the visible values consistently fall within the range reported in the paper (0.002–0.056 ms). This live terminal output serves as supplementary visual evidence; the pure-NLU benchmark script above (`benchmark/jarvis_nlu_pure_benchmark.py`, n=10,000) is provided as the primary, fully reproducible dataset for verification.

  ---

  ## Extension Direction — Patent 2 (Not the Focus of This Repository)

  While refining Patent 1, a deeper question was identified: *software-level isolation still cannot fully address physical-layer attacks*. This led to a second patent proposal based on thermodynamic entropy and nanosecond-scale physical short-circuit defense (patent pending, **not yet hardware-validated**).

  See `patent/patent2_future_direction.md` for a brief conceptual outline. This is explicitly a forward-looking idea, not a validated result, and is kept separate from the main narrative of this repository.

  ---

  ## Commercialization Exploration — Route 2 (Brief Summary)

  This architecture was submitted to the *"Yanyuan · Co-Creator" AI+ International Startup Competition (SynNovator)*, organized by Peking University Shanghai Lingang International Science and Innovation Center, as a proposed AI security plugin. It did not win an award in the offline finals, but through a referral from the Lingang Administrative Committee's Data Department, obtained preliminary admission eligibility to the "Zero Cube" ("零界魔方") incubator and signed a letter of intent.

  During subsequent commercialization efforts, it became clear that current team resources and go-to-market capability were insufficient to independently sustain the venture. The admission process was voluntarily terminated in order to refocus on core technical R&D.

  It was during this commercialization phase — separate from the patent/paper architecture above — that a Qwen2.5-1.5B based conversational NLU was experimented with, as part of exploring a more general-purpose AI security assistant concept. This experiment revealed significant latency trade-offs compared to the deterministic rule-based approach used in the patented system, reinforcing the design rationale of Route 1.

  See `docs/route2_exploration.md` for details and limitations of this phase.

  ---

  ## Demo Video

  - `prototype/demo_video_route1.mp4`: Full physical fusing trigger sequence, including terminal-side NLU latency logging.
  - Note: The demo video's on-screen title uses the working title "AirGap-Hub" (April 2026), used prior to the project being formalized under its current name for the IEEE paper submission.

  ---

  ## Citation

  If you use this work, please cite:

  > Y. Chen and M. Zha, "Edge-Assisted Smart Home Gateway with Hardware-Level
  > Air-Gap for Deterministic Privacy," in Proc. 2026 Int. Conf. Generative
  > Artificial Intelligence and Information Security (GAIIS), Wuhan, China,
  > Mar. 2026, doi: 10.1109/GAIIS69281.2026.11519263.
