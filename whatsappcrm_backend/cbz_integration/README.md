CBZ/iVeri integration notes

Status mapping

- Approved: `ResultCode == "0"` and `Status == "Approved"`
- Pending: `ResultCode == "0"` and `Status == "Pending"`
- Declined/failed: any other non-exception response, or explicit callback/query result that is not approved

Why this is strict

- The repository already models asynchronous EcoCash completion through callback and query endpoints.
- Public iVeri pages confirm transaction lookup/backoffice support, but they do not expose a complete public REST status taxonomy.
- Because of that, the code intentionally treats only the explicitly documented value `Pending` as pending, rather than guessing that every non-approved success code is still in progress.

Operational note

- If CBZ/iVeri provides a private merchant/developer guide with additional transient statuses, update `IVeriClient.is_pending()` in [services.py](services.py) to include only those exact values.