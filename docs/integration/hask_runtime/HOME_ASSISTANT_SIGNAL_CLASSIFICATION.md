# Home Assistant Signal Classification

Each of the 50 documented capabilities has exactly one primary classification:

- `AUTHORITATIVE_FACT`: 15 — the value explicitly reports an API/configuration/validation/registry fact.
- `STRUCTURED_CONTEXT_DEPENDENT`: 13 — structured data is real, but diagnosis requires context.
- `UNSAFE_INFERENCE`: 1 — service-call changed states cannot establish causality.
- `NOT_USABLE`: 21 — mutating, secret-bearing, media/free-text, redundant, or operational-only capabilities.

Observed undocumented commands are kept outside this classification denominator and labelled `OBSERVED_UNDOCUMENTED`. Observation cannot promote them to authority.

An authoritative state value proves only that Home Assistant reported that value at the sampled time. It does not prove a device, network, credential, integration, or root cause. Registry identifiers prove current registry relationships, not operational health.

