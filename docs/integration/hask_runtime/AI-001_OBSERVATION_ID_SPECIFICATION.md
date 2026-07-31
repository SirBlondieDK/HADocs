# AI-001 Observation ID Specification

## Format and construction

`observation_id` grammar is `obs1_[0-9a-f]{64}`; length 69 ASCII bytes.

Let `frame(s)` be `uint32_be(len(NFC(s).encode("utf-8"))) || NFC(s).encode("utf-8")`. Reject a framed value longer than 4,294,967,295 bytes. Construct:

```text
input = frame("hadocs-generic-metadata/observation-id/v1")
     || frame(installation_scope)
     || frame(source_capability)
     || frame(canonical_key)
digest = SHA-256(input)
observation_id = "obs1_" || lowercase_hex(digest)
```

The four fields and order are fixed. Category is already inside `canonical_key`; it is not framed separately. Contract version is not an input; the identity format is versioned by domain string and prefix. Compatible updates preserve format 1.

## Test vectors

Using installation scope `is1_32436db68321f2c10914ad6baf58257d5bf5275a5d537bc145cc8624a614f194`:

| Category | Source capability | Canonical key | Expected ID |
|---|---|---|---|
| API | `rest.api_root` | `ck1:api_availability:rest_api_root` | `obs1_90cbe1026ff98c538ec18854829293d38349ca802779bc8d362e948a9481dbcd` |
| Component | `rest.components` | `ck1:loaded_component:mqtt` | `obs1_79927229da53e5b9d0b9b2e503f769329d20e7a475285cb24553ee70e903e713` |
| Event | `rest.events` | `ck1:registered_event_type:state_changed` | `obs1_864d18c0e05d48fc16c99ddd83fc371057b8b8612b0a4010ea6e02baa4046b79` |
| Entity | `websocket.entity_registry.list_for_display` | `ck1:entity_display_reference:ref1_entity_d26423e92d0995348b23e8a0bab951fd9696898a0230020d11896033125b0f92` | `obs1_2916c20e0c01a5b72588d693da87368aafdf654d80ab083eca3a0c26bb40b3c3` |

The normative framed-input hex for the API vector is:

`000000296861646f63732d67656e657269632d6d657461646174612f6f62736572766174696f6e2d69642f7631000000446973315f333234333664623638333231663263313039313461643662616635383235376435626635323735613564353337626331343563633836323461363134663139340000000d726573742e6170695f726f6f7400000022636b313a6170695f617661696c6162696c6974793a726573745f6170695f726f6f74`

Invalid: uppercase digest, wrong prefix/length, non-NFC inputs, unknown source capability, malformed canonical key or absent scope.

Recompute from normative inputs on every snapshot. Equal input must yield equal ID. If one digest maps to unequal normalized input tuples, reject the whole new snapshot with `invalid_response`; never suffix, truncate differently or retry with another hash. Relationships use the validated ID rules defined by the relationship specification.

