# Generated by Django 5.1.4 on 2025-06-17 21:20

import django.db.models.deletion
import workspace.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Workspace',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('avatar_background', models.CharField(blank=True, default='#ffffff', max_length=7, null=True, validators=[workspace.models.validate_hex_color])),
                ('avatar_emoji', models.CharField(default='🚀', max_length=3)),
                ('avatar_image', models.ImageField(blank=True, null=True, upload_to='workspaces/')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date of create')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date of update')),
                ('is_active', models.BooleanField(default=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workspace_owner', to=settings.AUTH_USER_MODEL, verbose_name='Owner')),
            ],
        ),
        migrations.CreateModel(
            name='WorkspaceRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Name of role')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descriotion of role')),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='roles', to='workspace.workspace', verbose_name='Workspace')),
            ],
        ),
        migrations.CreateModel(
            name='WorkspaceMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('joined_at', models.DateTimeField(auto_now_add=True, verbose_name='Date of joined')),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workspace_memberships', to=settings.AUTH_USER_MODEL, verbose_name='User')),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='workspace.workspace', verbose_name='Workspace')),
                ('role', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='memberships', to='workspace.workspacerole', verbose_name='Role')),
            ],
            options={
                'unique_together': {('user', 'workspace')},
            },
        ),
    ]
