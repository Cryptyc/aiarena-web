# Generated by Django 4.2.17 on 2025-06-09 05:19

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0081_remove_result_date_interest_rating_calculated_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="competitionparticipation",
            unique_together={("competition", "bot")},
        ),
    ]
