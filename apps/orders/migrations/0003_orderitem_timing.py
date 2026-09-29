# Generated manually for prep/service time tracking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_table_assigned_waiter_table_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='preparing_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='ready_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='served_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
