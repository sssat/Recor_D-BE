from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0004_add_color'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schedule',
            name='type',
            field=models.CharField(
                choices=[
                    ('meeting', '회의'),
                    ('deadline', '마감일'),
                    ('presentation', '발표'),
                    ('other', '기타'),
                ],
                default='other',
                max_length=20,
            ),
        ),
    ]
