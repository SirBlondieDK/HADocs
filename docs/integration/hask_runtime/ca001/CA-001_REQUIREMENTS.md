# CA-001 Requirements

## Classification

These requirements are derived from existing authority or directly required to make that authority independently implementable. They are evaluation requirements, not selected design semantics.

## Security requirements

- A private installation-local secret must participate in opaque-reference derivation.
- Public installation scope alone must be insufficient to reproduce private reference derivation.
- Raw source identifiers and secret material must never appear in public output, logs or diagnostics.
- The design must resist practical recovery and offline confirmation of sensitive source identifiers by an output-only observer.
- The design must provide collision resistance appropriate to stable identity use.
- Cryptographic failures must be deterministic and fail closed for the affected capability.

## Determinism and interoperability

- Independent conforming producers given the same normative inputs must produce identical output bytes.
- Every input, its ordering, encoding, normalization, framing and domain separation must eventually be specified.
- Output grammar, encoding, length and validation must eventually be specified.
- Repeated derivation with the same preserved installation privacy context and source identity must remain stable.
- Different installation privacy contexts must not intentionally yield correlatable public references.
- No timestamp, traversal order, hostname, address, process state or consumer-selected value may determine identity.

## Secret lifecycle requirements

- Secret ownership, creation authority, generation quality, persistence and access boundary must eventually be normative.
- Backup, restore, migration, rotation, loss, corruption and recovery consequences must eventually be explicit.
- Ordinary restart and compatible update must not silently rotate a stable secret.
- Secret loss or corruption must never cause raw identifiers or a weaker derivation to be emitted.
- No external key-management or network service may be required.

## Compatibility requirements

- CA-001 must inventory effects on existing `ref1_`, canonical key, observation ID, relationship ID and installation scope semantics without modifying those artifacts.
- Any changed public bytes require explicit version and migration treatment.
- The active contract remains `1.0.0`; this architecture cannot activate a successor.
- Historical artifacts and identifiers remain interpretable as historical evidence.

## Verification requirements

- Synthetic secrets and identifiers only.
- Positive determinism, secret separation, installation separation, invalid-input and collision-response cases must eventually be testable.
- Normative vectors must be reproducible independently twice.
- Security claims must be bounded to the selected construction and documented threat model.

## Scope requirements

CA-001 must recommend exactly one complete cryptographic architecture only after alternatives are evaluated. It must distinguish inherited requirements from newly proposed choices. This Batch 1 document deliberately makes no selection.

