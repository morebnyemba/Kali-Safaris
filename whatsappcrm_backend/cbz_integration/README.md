# CBZ/iVeri integration notes

REST credential note

- This integration uses the iVeri REST transactions endpoint with `CertificateID`, `ApplicationID`, portal URL, and mode.
- `CertificateID` can be generated and rotated through the SOAP certificate lifecycle endpoints added under `/crm-api/payments/cbz/certificates/`.

Certificate lifecycle endpoints

- `POST /crm-api/payments/cbz/certificates/generate/` generates a new `CertificateID` and stores it on the active `CBZConfig`.
- `GET /crm-api/payments/cbz/certificates/current/` fetches the current certificate content from the SOAP API.
- `POST /crm-api/payments/cbz/certificates/submit/` submits a device certificate or CSR.
- `POST /crm-api/payments/cbz/certificates/renew/` renews the active `CertificateID` and stores the new value on the active `CBZConfig`.

SOAP lifecycle configuration

- Configure `CBZ_CERTIFICATE_SOAP_URL`, `CBZ_CERTIFICATE_SOAP_NAMESPACE`, `CBZ_CERTIFICATE_SOAP_ACTION_BASE`, `CBZ_CERTIFICATE_SOAP_USERNAME`, `CBZ_CERTIFICATE_SOAP_PASSWORD`, `CBZ_CERTIFICATE_MERCHANT_ID`, and `CBZ_CERTIFICATE_TERMINAL_ID` in the Django environment before using the lifecycle endpoints.
- The SOAP request body uses the documented lifecycle method names: `GenerateCertificateID`, `GetCertificate`, `SubmitCertificate`, and `RenewCertificateID`.

Test command

- Run the CBZ test suite without Postgres or Redis by using the dedicated test settings module:
  `powershell -Command "$env:DJANGO_SETTINGS_MODULE='whatsappcrm_backend.settings_test'; python manage.py test cbz_integration.tests"`

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
