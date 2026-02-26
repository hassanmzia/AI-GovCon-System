from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("opportunities", "0002_opportunityamendment_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="opportunity",
            name="source_url",
            field=models.URLField(blank=True, max_length=2000),
        ),
    ]
