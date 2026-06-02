"""
Migration 0004: Add new fields to CBZTransaction for full iVeri data persistence.

New fields:
  - bank_reference    : bank reference returned by acquiring bank
  - consumer_order_id : consumer-facing order ID from iVeri
  - card_bin          : first 6 digits of card (PCI-safe, identifies network)
  - gateway_response  : raw JSON payload from iVeri (PCI-scrubbed)
  - idempotency_key   : client-supplied dedup key (unique, nullable)
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cbz_integration', '0003_alter_cbztransaction_result_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='cbztransaction',
            name='bank_reference',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=100,
                help_text='Bank reference number returned by iVeri/acquiring bank',
            ),
        ),
        migrations.AddField(
            model_name='cbztransaction',
            name='consumer_order_id',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=100,
                help_text='Consumer-facing order ID from iVeri response',
            ),
        ),
        migrations.AddField(
            model_name='cbztransaction',
            name='card_bin',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=10,
                help_text='Card BIN (first 6 digits) — identifies card network/issuer',
            ),
        ),
        migrations.AddField(
            model_name='cbztransaction',
            name='gateway_response',
            field=models.JSONField(
                blank=True,
                null=True,
                help_text='Raw iVeri response payload for audit purposes (PCI-scrubbed)',
            ),
        ),
        migrations.AddField(
            model_name='cbztransaction',
            name='idempotency_key',
            field=models.CharField(
                blank=True,
                null=True,
                unique=True,
                max_length=64,
                db_index=True,
                help_text='Client-supplied idempotency key to prevent duplicate transactions',
            ),
        ),
    ]
