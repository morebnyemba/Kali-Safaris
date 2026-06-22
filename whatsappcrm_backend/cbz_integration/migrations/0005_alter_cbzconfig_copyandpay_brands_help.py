from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cbz_integration', '0004_cbztransaction_new_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cbzconfig',
            name='copyandpay_brands',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=255,
                help_text='Space-separated brands exposed by paymentWidgets (e.g. VISA MASTER AMEX PRIVATE_LABEL). PRIVATE_LABEL covers ZimSwitch private-label cards. Only brands enabled on your CBZ merchant account will appear in the widget.',
            ),
        ),
    ]
