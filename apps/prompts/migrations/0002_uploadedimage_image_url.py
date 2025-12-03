from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadedimage',
            name='image_url',
            field=models.URLField(blank=True),
        ),
        migrations.AlterField(
            model_name='uploadedimage',
            name='file',
            field=models.ImageField(blank=True, null=True, upload_to='users/%(user_id)s/uploads/'),
        ),
    ]