# Route 2 — Commercialization Exploration (Lingang Startup Competition)

## Background

While the core technical architecture (Route 1) was being validated for the patent and IEEE paper,
a parallel exploration was conducted to assess the commercial viability of repackaging this
air-gap security architecture as a general-purpose "AI security plugin" for smart home /
edge-AI products.

## Timeline

- Submitted to the **"Yanyuan · Co-Creator" AI+ International Startup Competition (SynNovator)**,
  organized by Peking University Shanghai Lingang International Science and Innovation Center.
- Did not receive an award in the offline finals.
- Through a referral from the **Lingang Administrative Committee's Data Department**, obtained
  preliminary admission eligibility to the **"Zero Cube" ("零界魔方") incubator** and signed a
  letter of intent.
- During this phase, a **Qwen2.5-1.5B**-based conversational NLU module was experimented with,
  as a more general-purpose alternative to the deterministic rule-based NLU used in Route 1.
  This was purely an exploratory branch, separate from the patented architecture.

## Key Findings / Why It Was Terminated

1. **Latency trade-off**: The LLM-based NLU introduced non-deterministic, higher-latency
   response times compared to the rule-based engine used in the patented system — reinforcing
   the design rationale for choosing a deterministic approach in safety-critical local control.
2. **Resource mismatch**: A one-person team (self-funded, no co-founders, no dedicated
   go-to-market resources) was not sufficient to independently sustain a hardware-software
   startup at this stage.
3. **Decision**: The incubator admission process was **voluntarily terminated**, and focus was
   redirected back to deepening the core security architecture (Route 1) and academic output.

## Takeaway

This exploration, while not resulting in a commercial outcome, provided a valuable real-world
comparison between LLM-based and rule-based edge NLU design choices, and confirmed that the
deterministic approach was the correct engineering decision for the target use case
(privacy-critical, latency-sensitive local control).
