from django.db import migrations, models


def move_todo_status_to_in_progress(apps, schema_editor):
    Todo = apps.get_model('todos', 'Todo')
    Todo.objects.filter(status='todo').update(status='in_progress')


class Migration(migrations.Migration):

    dependencies = [
        ('todos', '0003_project_on_delete_set_null'),
    ]

    operations = [
        migrations.RunPython(move_todo_status_to_in_progress, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='todo',
            name='status',
            field=models.CharField(
                choices=[('in_progress', '진행 중'), ('done', '완료')],
                default='in_progress',
                max_length=20,
            ),
        ),
    ]
