from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cbz_integration', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cbzconfig',
            name='copyandpay_base_url',
            field=models.URLField(
                blank=True,
                help_text='COPYandPAY base URL, e.g. https://eu-test.oppwa.com',
                max_length=500,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='cbzconfig',
            name='copyandpay_entity_id',
            field=models.CharField(
                blank=True,
                help_text='COPYandPAY entityId for checkout preparation',
                max_length=120,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='cbzconfig',
            name='copyandpay_bearer_token',
            field=models.CharField(
                blank=True,
                help_text='Authorization bearer token used for COPYandPAY API calls',
                max_length=512,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='cbzconfig',
            name='copyandpay_test_mode',
            field=models.CharField(
                blank=True,
                help_text='Optional testMode value (for example EXTERNAL)',
                max_length=32,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='cbzconfig',
            name='copyandpay_brands',
            field=models.CharField(
                blank=True,
                help_text='Space-separated brands exposed by paymentWidgets (e.g. VISA MASTER AMEX)',
                max_length=255,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='cbzconfig',
            name='copyandpay_widget_integrity',
            field=models.CharField(
                blank=True,
                help_text='Optional SRI integrity hash for paymentWidgets.js',
                max_length=512,
                null=True,
            ),
        ),
    ]
