from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0003_project_on_delete_set_null'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='color',
            field=models.CharField(
                choices=[
                    ('primary', '기본'),
                    ('green', '초록'),
                    ('yellow', '노랑'),
                    ('teal', '청록'),
                    ('red', '빨강'),
                ],
                default='primary',
                max_length=20,
            ),
        ),
    ]
