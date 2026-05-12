from django.db import migrations, models


def move_primary_color_to_green(apps, schema_editor):
    Schedule = apps.get_model('schedules', 'Schedule')
    Schedule.objects.filter(color='primary').update(color='green')


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0005_alter_schedule_type'),
    ]

    operations = [
        migrations.RunPython(move_primary_color_to_green, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='schedule',
            name='color',
            field=models.CharField(
                choices=[
                    ('green', 'green'),
                    ('blue', 'blue'),
                    ('teal', 'teal'),
                    ('yellow', 'yellow'),
                    ('brightGreen', 'brightGreen'),
                    ('red', 'red'),
                ],
                default='green',
                max_length=20,
            ),
        ),
    ]
