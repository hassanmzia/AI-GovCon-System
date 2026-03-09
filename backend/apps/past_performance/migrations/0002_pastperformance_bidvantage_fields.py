from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("past_performance", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="pastperformance",
            name="subcontract_number",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="pastperformance",
            name="technical_poc_name",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name="pastperformance",
            name="technical_poc_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="pastperformance",
            name="technical_poc_phone",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="pastperformance",
            name="relevance_summary",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="pastperformance",
            name="performance_summary",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="pastperformance",
            name="scope_of_work_bullets",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="pastperformance",
            name="role_on_contract",
            field=models.CharField(
                blank=True,
                choices=[
                    ("prime", "Prime Contractor"),
                    ("sub", "Subcontractor"),
                    ("jv", "Joint Venture Partner"),
                    ("team", "Teaming Partner"),
                ],
                max_length=20,
            ),
        ),
    ]
