

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myfarmacia', '0004_perfildador'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dador',
            name='ultimaDoacao',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.DeleteModel(
            name='PerfilDador',
        ),
    ]
