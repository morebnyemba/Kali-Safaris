"""
Management command: export_uat_report

Produces a structured export of CBZTransaction records suitable for submission
to iVeri/CBZ as UAT evidence for go-live approval.

Output formats:
  JSON  — one record per line (default), or pretty-printed with --pretty
  CSV   — flat spreadsheet row per transaction

Usage:
    python manage.py export_uat_report
    python manage.py export_uat_report --format=csv --output=uat_evidence.csv
    python manage.py export_uat_report --format=json --pretty --output=uat_report.json
    python manage.py export_uat_report --since=2025-01-01 --status=APPROVED,DECLINED
    python manage.py export_uat_report --include-gateway-response
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone as dj_tz


class Command(BaseCommand):
    help = (
        "Export CBZ/iVeri transaction records for UAT go-live submission. "
        "Produces JSON or CSV evidence for iVeri acceptance testing."
    )

    # Fields included in the export by default (PCI-safe — no full PAN / CVV)
    _EXPORT_FIELDS = [
        "id",
        "merchant_reference",
        "transaction_index",
        "request_id",
        "payment_type",
        "msisdn",
        "masked_pan",
        "amount",
        "currency",
        "command",
        "status",
        "result_code",
        "result_description",
        "authorisation_code",
        "bank_reference",
        "consumer_order_id",
        "card_bin",
        "idempotency_key",
        "booking_id",
        "created_at",
        "updated_at",
        "completed_at",
    ]

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--format",
            choices=["json", "csv"],
            default="json",
            help="Output format: json (default) or csv",
        )
        parser.add_argument(
            "--output",
            metavar="FILE",
            default=None,
            help="Write output to FILE instead of stdout",
        )
        parser.add_argument(
            "--pretty",
            action="store_true",
            default=False,
            help="Pretty-print JSON output (ignored for CSV)",
        )
        parser.add_argument(
            "--status",
            metavar="STATUS[,STATUS…]",
            default=None,
            help=(
                "Comma-separated list of statuses to include "
                "(e.g. APPROVED,DECLINED). Omit for all statuses."
            ),
        )
        parser.add_argument(
            "--payment-type",
            metavar="TYPE",
            choices=["ecocash", "card"],
            default=None,
            help="Filter by payment type: ecocash or card",
        )
        parser.add_argument(
            "--since",
            metavar="YYYY-MM-DD",
            default=None,
            help="Only include transactions created on or after this date",
        )
        parser.add_argument(
            "--until",
            metavar="YYYY-MM-DD",
            default=None,
            help="Only include transactions created on or before this date",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of records to export",
        )
        parser.add_argument(
            "--include-gateway-response",
            action="store_true",
            default=False,
            help=(
                "Include the raw gateway_response JSON blob in the export. "
                "Useful for detailed iVeri review. Already PCI-scrubbed."
            ),
        )

    # ─── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _parse_date(value: str, field_name: str) -> datetime:
        try:
            dt = datetime.strptime(value, "%Y-%m-%d")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            raise CommandError(
                f"--{field_name}: '{value}' is not a valid date (expected YYYY-MM-DD)"
            )

    @staticmethod
    def _serialize_value(v: Any) -> Any:
        """Make a value JSON-serializable."""
        if v is None:
            return None
        if hasattr(v, "isoformat"):
            return v.isoformat()
        if hasattr(v, "__str__") and not isinstance(v, (int, float, bool, str, dict, list)):
            return str(v)
        return v

    def _transaction_to_dict(
        self, txn: Any, include_gateway_response: bool
    ) -> Dict[str, Any]:
        fields = list(self._EXPORT_FIELDS)
        if include_gateway_response:
            fields.append("gateway_response")

        row: Dict[str, Any] = {}
        for field in fields:
            raw = getattr(txn, field, None)
            row[field] = self._serialize_value(raw)
        return row

    # ─── Main handle ──────────────────────────────────────────────────

    def handle(self, *args: Any, **options: Any) -> None:
        from cbz_integration.models import CBZTransaction  # noqa: PLC0415

        qs = CBZTransaction.objects.select_related("booking").order_by("created_at")

        # ── Filters ──
        if options["status"]:
            statuses = [s.strip().upper() for s in options["status"].split(",")]
            valid = {c[0] for c in CBZTransaction.TransactionStatus.choices}
            invalid = [s for s in statuses if s not in valid]
            if invalid:
                raise CommandError(
                    f"Unknown status values: {', '.join(invalid)}. "
                    f"Valid choices: {', '.join(sorted(valid))}"
                )
            qs = qs.filter(status__in=statuses)

        if options["payment_type"]:
            qs = qs.filter(payment_type=options["payment_type"])

        if options["since"]:
            since_dt = self._parse_date(options["since"], "since")
            qs = qs.filter(created_at__gte=since_dt)

        if options["until"]:
            until_dt = self._parse_date(options["until"], "until")
            qs = qs.filter(created_at__date__lte=until_dt.date())

        if options["limit"]:
            qs = qs[: options["limit"]]

        # ── Serialise ──
        records: List[Dict[str, Any]] = [
            self._transaction_to_dict(txn, options["include_gateway_response"])
            for txn in qs
        ]

        total = len(records)
        approved = sum(1 for r in records if r.get("status") == "APPROVED")
        declined = sum(1 for r in records if r.get("status") == "DECLINED")
        failed = sum(1 for r in records if r.get("status") in ("FAILED", "PENDING", "INITIATED"))

        # ── Write ──
        fmt = options["format"]
        outfile = options["output"]

        if fmt == "json":
            self._write_json(records, outfile, options["pretty"])
        else:
            self._write_csv(records, outfile, options["include_gateway_response"])

        # Summary to stderr so it doesn't pollute stdout/file output
        summary_lines = [
            "",
            "── UAT Export Summary ──────────────────────────",
            f"  Total records  : {total}",
            f"  Approved       : {approved}",
            f"  Declined       : {declined}",
            f"  Pending/Failed : {failed}",
            f"  Format         : {fmt.upper()}",
            f"  Output         : {outfile or 'stdout'}",
            f"  Generated at   : {dj_tz.now().isoformat()}",
            "────────────────────────────────────────────────",
            "",
        ]
        self.stderr.write(self.style.SUCCESS("\n".join(summary_lines)))

    # ─── Output writers ───────────────────────────────────────────────

    def _write_json(
        self,
        records: List[Dict[str, Any]],
        outfile: Optional[str],
        pretty: bool,
    ) -> None:
        indent = 2 if pretty else None
        payload = {
            "generated_at": dj_tz.now().isoformat(),
            "record_count": len(records),
            "transactions": records,
        }
        text = json.dumps(payload, indent=indent, ensure_ascii=False)
        if outfile:
            with open(outfile, "w", encoding="utf-8") as fh:
                fh.write(text)
                fh.write("\n")
            self.stdout.write(f"Written to {outfile}")
        else:
            sys.stdout.write(text)
            sys.stdout.write("\n")

    def _write_csv(
        self,
        records: List[Dict[str, Any]],
        outfile: Optional[str],
        include_gateway_response: bool,
    ) -> None:
        if not records:
            self.stderr.write(self.style.WARNING("No records to export."))
            return

        fieldnames = list(records[0].keys())

        def _write(fh: Any) -> None:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for row in records:
                # Flatten gateway_response dict → JSON string for CSV cells
                if "gateway_response" in row and isinstance(row["gateway_response"], dict):
                    row = dict(row)
                    row["gateway_response"] = json.dumps(row["gateway_response"])
                writer.writerow(row)

        if outfile:
            with open(outfile, "w", newline="", encoding="utf-8") as fh:
                _write(fh)
            self.stdout.write(f"Written to {outfile}")
        else:
            import io
            buf = io.StringIO()
            _write(buf)
            sys.stdout.write(buf.getvalue())
