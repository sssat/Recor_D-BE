from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todos', '0004_update_status_choices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='todo',
            name='priority',
            field=models.CharField(
                choices=[('low', '낮음'), ('medium', '보통'), ('high', '높음')],
                default='medium',
                max_length=10,
            ),
        ),
    ]
