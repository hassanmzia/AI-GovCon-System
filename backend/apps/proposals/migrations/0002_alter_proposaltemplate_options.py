from django.db import migrations


class Migration(migrations.Migration):
    """Remove the auto-created ordering from ProposalTemplate Meta options
    to match the model definition which has no explicit ordering."""

    dependencies = [
        ("proposals", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="proposaltemplate",
            options={},
        ),
    ]
