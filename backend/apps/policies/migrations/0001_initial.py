# Generated migration for the policies app.
# Models: BusinessPolicy, PolicyRule, PolicyEvaluation, PolicyException

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("deals", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ------------------------------------------------------------------
        # BusinessPolicy
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="BusinessPolicy",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                (
                    "policy_type",
                    models.CharField(
                        choices=[
                            ("bid_threshold", "Bid Threshold"),
                            ("approval_gate", "Approval Gate"),
                            ("risk_limit", "Risk Limit"),
                            ("compliance_requirement", "Compliance Requirement"),
                            ("teaming_rule", "Teaming Rule"),
                            ("pricing_constraint", "Pricing Constraint"),
                        ],
                        db_index=True,
                        max_length=50,
                    ),
                ),
                (
                    "scope",
                    models.CharField(
                        choices=[
                            ("global", "Global"),
                            ("deal_type", "Deal Type"),
                            ("naics_code", "NAICS Code"),
                            ("agency", "Agency"),
                        ],
                        db_index=True,
                        default="global",
                        max_length=50,
                    ),
                ),
                ("conditions", models.JSONField(default=dict)),
                ("actions", models.JSONField(default=dict)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("priority", models.PositiveIntegerField(default=100)),
                ("effective_date", models.DateField(blank=True, null=True)),
                ("expiry_date", models.DateField(blank=True, null=True)),
                ("version", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_policies",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Business Policy",
                "verbose_name_plural": "Business Policies",
                "ordering": ["priority", "name"],
            },
        ),
        migrations.AddIndex(
            model_name="businesspolicy",
            index=models.Index(
                fields=["is_active", "policy_type"],
                name="policies_bp_active_type_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="businesspolicy",
            index=models.Index(
                fields=["scope", "is_active"],
                name="policies_bp_scope_active_idx",
            ),
        ),
        # ------------------------------------------------------------------
        # PolicyRule
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="PolicyRule",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("rule_name", models.CharField(max_length=255)),
                ("field_path", models.CharField(max_length=255)),
                (
                    "operator",
                    models.CharField(
                        choices=[
                            ("gt", "Greater Than"),
                            ("lt", "Less Than"),
                            ("eq", "Equal To"),
                            ("gte", "Greater Than or Equal To"),
                            ("lte", "Less Than or Equal To"),
                            ("in", "In List"),
                            ("not_in", "Not In List"),
                            ("contains", "Contains"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "threshold_value",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                ("threshold_json", models.JSONField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True, default="")),
                ("warning_message", models.TextField(blank=True, default="")),
                ("is_blocking", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "policy",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rules",
                        to="policies.businesspolicy",
                    ),
                ),
            ],
            options={
                "verbose_name": "Policy Rule",
                "verbose_name_plural": "Policy Rules",
                "ordering": ["policy", "rule_name"],
            },
        ),
        # ------------------------------------------------------------------
        # PolicyEvaluation
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="PolicyEvaluation",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "evaluated_at",
                    models.DateTimeField(
                        db_index=True, default=django.utils.timezone.now
                    ),
                ),
                (
                    "outcome",
                    models.CharField(
                        choices=[
                            ("pass", "Pass"),
                            ("warn", "Warn"),
                            ("fail", "Fail"),
                            ("skip", "Skip"),
                        ],
                        db_index=True,
                        max_length=10,
                    ),
                ),
                ("triggered_rules", models.JSONField(default=list)),
                ("recommendations", models.JSONField(default=list)),
                ("auto_resolved", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "deal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="policy_evaluations",
                        to="deals.deal",
                    ),
                ),
                (
                    "policy",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evaluations",
                        to="policies.businesspolicy",
                    ),
                ),
                (
                    "resolved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="resolved_evaluations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Policy Evaluation",
                "verbose_name_plural": "Policy Evaluations",
                "ordering": ["-evaluated_at"],
            },
        ),
        migrations.AddIndex(
            model_name="policyevaluation",
            index=models.Index(
                fields=["deal", "outcome"],
                name="policies_pe_deal_outcome_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="policyevaluation",
            index=models.Index(
                fields=["policy", "evaluated_at"],
                name="policies_pe_policy_evat_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="policyevaluation",
            index=models.Index(
                fields=["deal", "policy", "-evaluated_at"],
                name="policies_pe_deal_pol_evat_idx",
            ),
        ),
        # ------------------------------------------------------------------
        # PolicyException
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="PolicyException",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("reason", models.TextField()),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "approved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approved_policy_exceptions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "deal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="policy_exceptions",
                        to="deals.deal",
                    ),
                ),
                (
                    "policy",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="exceptions",
                        to="policies.businesspolicy",
                    ),
                ),
                (
                    "requested_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="requested_policy_exceptions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Policy Exception",
                "verbose_name_plural": "Policy Exceptions",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="policyexception",
            index=models.Index(
                fields=["status", "expires_at"],
                name="policies_pex_status_exp_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="policyexception",
            index=models.Index(
                fields=["deal", "policy", "status"],
                name="policies_pex_deal_pol_sts_idx",
            ),
        ),
    ]
