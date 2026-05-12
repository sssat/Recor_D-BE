import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_update_status_and_color_choices'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name='project',
            old_name='owner',
            new_name='user',
        ),
        migrations.AlterField(
            model_name='project',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='projects',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
