from pathlib import Path
import json

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime

from accounts.models import User
from workspace.models import Workspace, WorkspaceRole, WorkspaceMember
from project.models import Project, ProjectMember


class Command(BaseCommand):
    """
    Django management command to load test data from JSON fixtures using the ORM.

    Supported files (loaded in order):
        - user.json
        - workspace.json
        - workspace_member.json

    Usage:
        python manage.py load_test_data
        python manage.py load_test_data --only user.json
    """

    help = "Loads test JSON data into the database using ORM in the correct order."

    def add_arguments(self, parser):
        parser.add_argument(
            '--only',
            type=str,
            help="Specify a single JSON fixture file to load (e.g., user.json)"
        )

    def handle(self, *args, **options):
        """
        Main entry point of the management command.
        Determines which files to load and delegates to respective methods.
        """
 
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        data_dir = base_dir / "test_db_data"

        if not data_dir.exists():
            raise CommandError(f"Directory '{data_dir}' not found.")

        file_to_method = {
            "user.json": self.load_users,
            "workspace.json": self.load_workspaces,
            "workspace_member.json": self.load_workspace_members,
            "project.json": self.load_projects,
            "project_member.json": self.load_projects_member,
        }

        if options["only"]:
            only = options["only"].lower()
            if only not in file_to_method:
                raise CommandError(f"Unknown file: {only}")
            files = [only]
        else:
            files = file_to_method.keys()

        for filename in files:
            path = data_dir / filename
            if not path.exists():
                self.stderr.write(self.style.WARNING(f"File {filename} not found. Skipping."))
                continue

            self.stdout.write(self.style.NOTICE(f"Loading {filename}..."))
            try:
                file_to_method[filename](path)
                self.stdout.write(self.style.SUCCESS(f"Loaded {filename} successfully."))
            except Exception as e:
                raise CommandError(f"Failed to load {filename}: {e}")

    def load_users(self, path: Path):
        """
        Loads users from JSON into the database using ORM.
        A default password 'test12345' is set for all users.
        """

        password = "test12345"

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            fields = entry["fields"]
            if User.objects.filter(email=fields["email"]).exists():
                continue

            user = User(
                email=fields["email"],
                first_name=fields.get("first_name", ""),
                last_name=fields.get("last_name", ""),
                bio=fields.get("bio"),
                avatar_background=fields.get("avatar_background"),
                avatar_emoji=fields.get("avatar_emoji", "🚀"),
                is_active=fields.get("is_active", True),
                is_staff=fields.get("is_staff", False),
                date_joined=parse_datetime(fields.get("date_joined")),
            )
            user.set_password(password)
            user.save()

    def load_workspaces(self, path: Path):
        """
        Loads workspaces from JSON into the database.
        The save() method creates roles automatically for each workspace.
        """

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            fields = entry["fields"]
            owner = User.objects.get(pk=fields["owner"])

            workspace = Workspace(
                name=fields["name"],
                description=fields.get("description"),
                currency=fields.get("currency"),
                avatar_background=fields.get("avatar_background"),
                avatar_emoji=fields.get("avatar_emoji", "🚀"),
                owner=owner,
                is_active=fields.get("is_active", True)
            )
            workspace.save()

    def load_workspace_members(self, path: Path):
        """
        Loads workspace members from JSON into the database.
        Resolves role by name per workspace and skips owners.
        """

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        created_count = 0
        for entry in data:
            fields = entry["fields"]

            workspace_id = fields["workspace"]
            user_id = fields["user"]
            role_name = fields["role"]  # "admin", "user", "client"

            try:
                workspace = Workspace.objects.get(pk=workspace_id)
            except Workspace.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Workspace {workspace_id} not found. Skipping."))
                continue

            if user_id == workspace.owner_id:
                role_name = "admin"

            try:
                role = WorkspaceRole.objects.get(workspace=workspace, name=role_name)
            except WorkspaceRole.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Role '{role_name}' not found in workspace {workspace_id}."))
                continue

            WorkspaceMember.objects.update_or_create(
                user_id=user_id,
                workspace=workspace,
                defaults={
                    "role": role,
                    "status": fields.get("status", "active"),
                    "hour_rate": fields.get("hour_rate"),
                    "joined_at": parse_datetime(fields.get("joined_at")),
                    "is_active": fields.get("is_active", True),
                }
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"{created_count} workspace members created."))

    def load_projects(self, path: Path):
        """
        Loads projects from JSON into the database.
        """

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        created_count = 0
        for entry in data:
            fields = entry["fields"]

            workspace = Workspace.objects.get(pk=fields.get("workspace"))
            owner = User.objects.get(pk=fields.get("owner"))

            project = Project(
                name=fields.get("name"),
                key=fields.get("key"),
                description=fields.get("description"),
                workspace=workspace,
                owner=owner,
                is_public=fields.get("is_public", True),
                is_billable=fields.get("is_billable", True),
                is_active=fields.get("is_active", True),
                avatar_background=fields.get("avatar_background"),
                avatar_emoji=fields.get("avatar_emoji", "🚀"),
                created_at=parse_datetime(fields.get("created_at")),
                updated_at=parse_datetime(fields.get("updated_at")),
            )
            project.save()
            created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"{created_count} projects created."))

    def load_projects_member(self, path: Path):
        """
        Loads project members from JSON into the database.
        """

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        created_count = 0
        for entry in data:
            fields = entry["fields"]

            project = Project.objects.get(pk=fields.get("project"))
            user = User.objects.get(pk=fields.get("user"))

            project = ProjectMember(
                user=user,
                project=project,
                is_active=fields.get("is_active", True),
                created_at=parse_datetime(fields.get("created_at")),
                updated_at=parse_datetime(fields.get("updated_at")),
            )
            project.save()
            created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"{created_count} project members created."))