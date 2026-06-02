"""
Management command: reconcile_payments

Queries iVeri for every PENDING/INITIATED CBZTransaction older than a configurable
age threshold, updates their status based on the gateway's answer, and prints a
reconciliation report.

Usage:
    python manage.py reconcile_payments
    python manage.py reconcile_payments --min-age-minutes=10 --dry-run
    python manage.py reconcile_payments --limit=200 --output=report.json
"""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict

from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Reconcile PENDING/INITIATED CBZ transactions against iVeri. "
        "Updates local status where the gateway has a definitive answer."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--min-age-minutes",
            type=int,
            default=5,
            help="Only reconcile transactions older than this many minutes (default: 5)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum number of transactions to process per run (default: 100)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Query iVeri but do not persist any status changes",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Write JSON reconciliation report to this file path",
        )

    def handle(self, *args: Any, **options: Any) -> None:  # noqa: C901
        from cbz_integration.models import CBZTransaction
        from cbz_integration.services import IVeriClient
        from cbz_integration.views import _record_payment  # shared helper

        min_age = options["min_age_minutes"]
        limit = options["limit"]
        dry_run = options["dry_run"]
        output_path = options.get("output")

        cutoff = timezone.now() - timedelta(minutes=min_age)

        qs = (
            CBZTransaction.objects
            .filter(
                status__in=[
                    CBZTransaction.TransactionStatus.PENDING,
                    CBZTransaction.TransactionStatus.INITIATED,
                ],
                created_at__lt=cutoff,
            )
            .select_related("booking")
            .order_by("created_at")[:limit]
        )

        count = qs.count()
        self.stdout.write(
            self.style.NOTICE(
                f"Reconciling {count} transaction(s) older than {min_age} min "
                f"{'[DRY RUN]' if dry_run else ''}"
            )
        )

        report: Dict[str, Any] = {
            "run_at": timezone.now().isoformat(),
            "dry_run": dry_run,
            "min_age_minutes": min_age,
            "limit": limit,
            "total_found": count,
            "results": [],
        }

        approved = declined = errors = skipped = 0

        for txn in qs:
            entry: Dict[str, Any] = {
                "merchant_reference": txn.merchant_reference,
                "payment_type": txn.payment_type,
                "amount": str(txn.amount),
                "currency": txn.currency,
                "old_status": txn.status,
                "new_status": None,
                "result_code": None,
                "error": None,
            }

            try:
                from cbz_integration.views import _build_client  # type: ignore[attr-defined]
                client = _build_client()
                response = client.query_transaction(merchant_reference=txn.merchant_reference)
                result = IVeriClient.get_result(response)

                entry["result_code"] = result.get("result_code")
                entry["status_label"] = result.get("status_label")

                is_approved = IVeriClient.is_approved(response)
                is_pending = IVeriClient.is_pending(response)

                if is_approved:
                    entry["new_status"] = CBZTransaction.TransactionStatus.APPROVED
                    if not dry_run:
                        txn.result_code = result.get("result_code")
                        txn.result_description = result.get("result_description")
                        txn.transaction_index = result.get("transaction_index") or txn.transaction_index
                        txn.authorisation_code = result.get("authorisation_code") or txn.authorisation_code
                        txn.bank_reference = result.get("bank_reference") or txn.bank_reference
                        txn.consumer_order_id = result.get("consumer_order_id") or txn.consumer_order_id
                        txn.card_bin = result.get("card_bin") or txn.card_bin
                        txn.status = CBZTransaction.TransactionStatus.APPROVED
                        txn.completed_at = timezone.now()
                        txn.save()
                        if txn.booking:
                            _record_payment(txn, txn.booking)
                        logger.info(
                            "Payment status changed",
                            extra={
                                "transaction_id": str(txn.id),
                                "merchant_reference": txn.merchant_reference,
                                "old_status": entry["old_status"],
                                "new_status": "APPROVED",
                                "gateway": "IVERI",
                                "source": "reconcile_payments",
                            },
                        )
                    approved += 1
                elif is_pending:
                    entry["new_status"] = "STILL_PENDING"
                    skipped += 1
                else:
                    entry["new_status"] = CBZTransaction.TransactionStatus.DECLINED
                    if not dry_run:
                        txn.result_code = result.get("result_code")
                        txn.result_description = result.get("result_description")
                        txn.status = CBZTransaction.TransactionStatus.DECLINED
                        txn.save()
                        logger.info(
                            "Payment status changed",
                            extra={
                                "transaction_id": str(txn.id),
                                "merchant_reference": txn.merchant_reference,
                                "old_status": entry["old_status"],
                                "new_status": "DECLINED",
                                "gateway": "IVERI",
                                "source": "reconcile_payments",
                                "result_code": result.get("result_code"),
                                "status_label": result.get("status_label"),
                            },
                        )
                    declined += 1

            except Exception as exc:
                entry["error"] = str(exc)
                errors += 1
                logger.exception(
                    "Reconciliation failed for %s: %s",
                    txn.merchant_reference, exc,
                )

            report["results"].append(entry)
            status_str = entry.get("new_status") or "unchanged"
            style = self.style.SUCCESS if is_approved else (
                self.style.WARNING if entry.get("error") else self.style.NOTICE
            )
            self.stdout.write(
                style(f"  {txn.merchant_reference}: {entry['old_status']} → {status_str}")
            )

        # ── Summary ──────────────────────────────────────────────────
        report["summary"] = {
            "approved": approved,
            "declined": declined,
            "still_pending": skipped,
            "errors": errors,
        }

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Reconciliation complete"))
        self.stdout.write(f"  Approved:       {approved}")
        self.stdout.write(f"  Declined:       {declined}")
        self.stdout.write(f"  Still pending:  {skipped}")
        self.stdout.write(f"  Errors:         {errors}")
        if dry_run:
            self.stdout.write(self.style.WARNING("  [DRY RUN — no changes persisted]"))

        if output_path:
            with open(output_path, "w", encoding="utf-8") as fh:
                json.dump(report, fh, indent=2, default=str)
            self.stdout.write(self.style.SUCCESS(f"  Report written to: {output_path}"))
