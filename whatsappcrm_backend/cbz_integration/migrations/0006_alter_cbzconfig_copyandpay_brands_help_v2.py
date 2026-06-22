from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cbz_integration', '0005_alter_cbzconfig_copyandpay_brands_help'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cbzconfig',
            name='copyandpay_brands',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=255,
                help_text='Space-separated brands exposed by paymentWidgets. This merchant entityId is provisioned by ZimSwitch as Private Label only (default: PRIVATE_LABEL). Only brands enabled on your CBZ merchant account will appear in the widget.',
            ),
        ),
    ]
