from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customer_data', '0008_add_paynow_payment_methods'),
    ]

    operations = [
        migrations.CreateModel(
            name='CBZConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Default', help_text="Configuration name for reference (e.g., 'Production', 'UAT')", max_length=100)),
                ('portal_url', models.URLField(default='https://portal.host.iveri.com', help_text='iVeri Gateway Portal URL', max_length=500)),
                ('certificate_id', models.CharField(blank=True, help_text='CertificateID (GUID) used by REST transactions. Can be generated via SOAP lifecycle tools.', max_length=100, null=True)),
                ('application_id', models.CharField(help_text='ApplicationID (GUID) assigned by the acquiring bank (CBZ)', max_length=100)),
                ('mode', models.CharField(choices=[('Test', 'Test / Sandbox'), ('LIVE', 'Live / Production')], default='Test', help_text='Transaction mode: Test for sandbox, LIVE for production', max_length=10)),
                ('is_active', models.BooleanField(default=True, help_text='Only one configuration can be active at a time')),
                ('callback_url', models.URLField(blank=True, help_text='URL for iVeri to send out-of-band transaction notifications (optional)', max_length=500, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'CBZ/iVeri Configuration',
                'verbose_name_plural': 'CBZ/iVeri Configurations',
                'ordering': ['-is_active', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CBZTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('merchant_reference', models.CharField(db_index=True, help_text='Unique merchant reference for this transaction', max_length=100, unique=True)),
                ('transaction_index', models.CharField(blank=True, help_text='iVeri TransactionIndex returned on success', max_length=100, null=True)),
                ('request_id', models.CharField(blank=True, help_text='iVeri RequestID for tracking', max_length=100, null=True)),
                ('payment_type', models.CharField(choices=[('ecocash', 'EcoCash'), ('card', 'Card (Visa/Mastercard)')], help_text='Type of payment: EcoCash or Card', max_length=10)),
                ('msisdn', models.CharField(blank=True, help_text='Mobile number for EcoCash payments (2637XXXXXXXX format)', max_length=20, null=True)),
                ('masked_pan', models.CharField(blank=True, help_text='Masked card PAN (e.g., 5413****0020) — for reference only', max_length=20, null=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(choices=[('USD', 'USD'), ('ZWG', 'ZWG')], max_length=3)),
                ('command', models.CharField(default='Debit', help_text='iVeri command (Debit, Authorisation, Credit, etc.)', max_length=20)),
                ('status', models.CharField(choices=[('INITIATED', 'Initiated'), ('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('DECLINED', 'Declined'), ('FAILED', 'Failed'), ('VOIDED', 'Voided'), ('REFUNDED', 'Refunded')], default='INITIATED', max_length=20)),
                ('result_code', models.CharField(blank=True, max_length=10, null=True)),
                ('result_description', models.TextField(blank=True, null=True)),
                ('authorisation_code', models.CharField(blank=True, max_length=20, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('booking', models.ForeignKey(blank=True, help_text='The booking this payment is for', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cbz_transactions', to='customer_data.booking')),
            ],
            options={
                'verbose_name': 'CBZ/iVeri Transaction',
                'verbose_name_plural': 'CBZ/iVeri Transactions',
                'ordering': ['-created_at'],
            },
        ),
    ]