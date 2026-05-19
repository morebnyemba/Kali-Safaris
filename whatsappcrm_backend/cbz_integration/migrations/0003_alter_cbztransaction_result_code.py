from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cbz_integration', '0002_cbzconfig_copyandpay_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cbztransaction',
            name='result_code',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]
