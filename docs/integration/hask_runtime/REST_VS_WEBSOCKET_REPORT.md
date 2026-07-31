# REST vs WebSocket Report

| Capability | Preferred source | Reason |
|---|---|---|
| Config/states | `EQUIVALENT` | Outer structures were observed through both; current HADocs already uses REST |
| Services | `EQUIVALENT` semantically | Containers differ; REST list versus WS domain map |
| Registry/topology | `PRIMARY_SOURCE: WebSocket` | Official registry commands and target resolution are WebSocket capabilities |
| History/logbook/calendars | `PRIMARY_SOURCE: REST` | Documented REST query interfaces |
| Events | REST for inventory; WS for stream | Snapshot listener counts versus subscriptions |
| Validation/targets | `PRIMARY_SOURCE: WebSocket` | Typed validation and target capability commands |
| Error logs/media/auth | `UNSUITABLE` | Privacy, secrets, or unstructured/binary data |

No source provides standardized integration connectivity.

