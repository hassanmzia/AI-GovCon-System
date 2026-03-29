from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_remove_notification_created_at_notification"),
    ]

    operations = [
        migrations.CreateModel(
            name="SystemSetting",
            fields=[
                (
                    "key",
                    models.CharField(
                        max_length=100,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("value", models.JSONField(default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["key"],
            },
        ),
    ]
