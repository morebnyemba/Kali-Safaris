"""
Management command: export_uat_report

Exports CBZTransaction records in the iVeri Lite log format required for UAT
go-live submission to iVeri/CBZ.

Output format (matches handy-hands_logs-iveri-lite.json reference):
  [
    {
      "status": "success",
      "message": "Payment was successful.",
      "gateway_response": { <LITE_* and ECOM_* fields> }
    },
    ...
  ]

Status mapping:
  LITE_PAYMENT_CARD_STATUS "0"   → status: "success"
  LITE_PAYMENT_CARD_STATUS "4"   → status: "fail"
  LITE_PAYMENT_CARD_STATUS "1"   → status: "error"
  LITE_PAYMENT_CARD_STATUS "255" → status: "error"

Usage:
    python manage.py export_uat_report
    python manage.py export_uat_report --output=uat_report.json
    python manage.py export_uat_report --status=APPROVED,DECLINED
    python manage.py export_uat_report --since=2025-01-01
    python manage.py export_uat_report --payment-type=card
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone as dj_tz


# Human-friendly labels for iVeri result codes
_RESULT_STATUS: Dict[str, tuple] = {
    "0":   ("success", "Payment was successful."),
    "4":   ("fail",    "Payment failed or was declined."),
    "1":   ("error",   "A system error occurred during payment."),
    "255": ("error",   "A system error occurred during payment."),
}
_DEFAULT_STATUS = ("error", "An unknown gateway error occurred.")


class Command(BaseCommand):
    help = (
        "Export CBZ/iVeri transaction records in iVeri Lite log format "
        "for UAT go-live submission to iVeri/CBZ."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--output",
            metavar="FILE",
            default=None,
            help="Write output to FILE instead of stdout",
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

    @staticmethod
    def _parse_date(value: str, field_name: str) -> datetime:
        try:
            dt = datetime.strptime(value, "%Y-%m-%d")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            raise CommandError(
                f"--{field_name}: '{value}' is not a valid date (expected YYYY-MM-DD)"
            )

    def _build_gateway_response(self, txn: Any, application_id: str) -> Dict[str, Any]:
        """
        Return a gateway_response dict in iVeri Lite format.

        If the transaction already has a stored gateway_response with LITE_*
        keys (from a real iVeri Lite callback), use that directly and ensure
        ECOM_PAYMENT_CARD_NUMBER is populated from masked_pan.

        Otherwise reconstruct from model fields (e.g. REST API transactions).
        """
        stored: Dict[str, Any] = txn.gateway_response or {}

        if "LITE_PAYMENT_CARD_STATUS" in stored:
            # Already in Lite format — use as-is, injecting masked_pan if stored
            gr = dict(stored)
            if txn.masked_pan and not gr.get("ECOM_PAYMENT_CARD_NUMBER"):
                gr["ECOM_PAYMENT_CARD_NUMBER"] = txn.masked_pan
            return gr

        # Reconstruct Lite-format dict from model fields
        amount_minor = ""
        try:
            if txn.amount is not None:
                amount_minor = str(int(float(txn.amount) * 100))
        except (ValueError, TypeError):
            pass

        created_str = ""
        if txn.created_at:
            created_str = txn.created_at.strftime("%Y-%m-%d %H:%M:%S")

        return {
            "LITE_MERCHANT_APPLICATIONID": application_id,
            "MERCHANTREFERENCE": txn.merchant_reference or "",
            "ECOM_CONSUMERORDERID": txn.consumer_order_id or txn.merchant_reference or "",
            "LITE_CONSUMERORDERID_PREFIX": "INV",
            "LITE_PAYMENT_CARD_STATUS": txn.result_code or "",
            "LITE_RESULT_DESCRIPTION": txn.result_description or "",
            "LITE_TRANSACTIONINDEX": txn.transaction_index or "",
            "LITE_TRANSACTIONDATE": created_str,
            "LITE_BANKREFERENCE": txn.bank_reference or "",
            "LITE_ORDER_AUTHORISATIONCODE": txn.authorisation_code or "",
            "LITE_PAYMENT_CARD_BIN": txn.card_bin or "",
            "LITE_ORDER_AMOUNT": amount_minor,
            "LITE_ORDER_LINEITEMS_AMOUNT_1": amount_minor,
            "LITE_ORDER_LINEITEMS_QUANTITY_1": "1",
            "LITE_ORDER_LINEITEMS_PRODUCT_1": "Order",
            "LITE_CURRENCY_ALPHACODE": txn.currency or "USD",
            "ECOM_PAYMENT_CARD_NUMBER": txn.masked_pan or "",
            "ECOM_PAYMENT_CARD_PROTOCOLS": "IVERI",
            "ECOM_TRANSACTIONCOMPLETE": "False",
        }

    def _transaction_to_record(self, txn: Any, application_id: str) -> Dict[str, Any]:
        result_code = txn.result_code or ""
        status_label, message = _RESULT_STATUS.get(result_code, _DEFAULT_STATUS)

        # Override status label from stored model status for non-terminal transactions
        if not result_code:
            if txn.status == "APPROVED":
                status_label, message = _RESULT_STATUS["0"]
            elif txn.status == "DECLINED":
                status_label, message = _RESULT_STATUS["4"]

        return {
            "status": status_label,
            "message": message,
            "gateway_response": self._build_gateway_response(txn, application_id),
        }

    def handle(self, *args: Any, **options: Any) -> None:
        from cbz_integration.models import CBZTransaction, CBZConfig  # noqa: PLC0415

        # Get application ID from active config (used in gateway_response reconstruction)
        config = CBZConfig.objects.filter(is_active=True).first()
        application_id = config.application_id if config else ""

        qs = CBZTransaction.objects.order_by("created_at")

        # ── Filters ──────────────────────────────────────────────────
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
            qs = qs.filter(created_at__gte=self._parse_date(options["since"], "since"))

        if options["until"]:
            qs = qs.filter(created_at__date__lte=self._parse_date(options["until"], "until").date())

        if options["limit"]:
            qs = qs[: options["limit"]]

        # ── Build output ──────────────────────────────────────────────
        records: List[Dict[str, Any]] = [
            self._transaction_to_record(txn, application_id) for txn in qs
        ]

        text = json.dumps(records, indent=2, ensure_ascii=False)

        outfile = options["output"]
        if outfile:
            with open(outfile, "w", encoding="utf-8") as fh:
                fh.write(text)
                fh.write("\n")
            self.stdout.write(self.style.SUCCESS(f"Written to {outfile}"))
        else:
            sys.stdout.write(text)
            sys.stdout.write("\n")

        # Summary to stderr
        approved = sum(1 for r in records if r["status"] == "success")
        failed = sum(1 for r in records if r["status"] == "fail")
        errored = sum(1 for r in records if r["status"] == "error")
        self.stderr.write(self.style.SUCCESS(
            f"\n── UAT Export ─────────────────────────────────\n"
            f"  Total    : {len(records)}\n"
            f"  Success  : {approved}\n"
            f"  Fail     : {failed}\n"
            f"  Error    : {errored}\n"
            f"  Output   : {outfile or 'stdout'}\n"
            f"  Generated: {dj_tz.now().isoformat()}\n"
            f"────────────────────────────────────────────────\n"
        ))
