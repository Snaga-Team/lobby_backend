# 🛠️ Lobby System Backend

This is a modular backend system for managing users, workspaces, projects, roles, and billing in a SaaS-like environment. The system is built using Django and Django REST Framework and is designed with scalability in mind using a centralized PostgreSQL database (with future support for database separation).

👉 For installation and setup instructions, see [INSTALL.md](INSTALL.md)

---

## 📌 User Roles and Permissions

Each workspace gets default user roles automatically upon creation:

| Role  | Title        | Description                                                   |
|-------|--------------|---------------------------------------------------------------|
| admin | Administrator| Full control. Assigned to the creator by default.             |
| user  | User         | Can view all projects, but cannot manage them.                |
| client| Client       | Limited access. Can only see selected projects.               |

### Default Role Definitions

```python
ROLE_ADMIN = {"name": "admin", "description": "Administrator of the workspace"}
ROLE_USER = {"name": "user", "description": "Regular user of the workspace"}
ROLE_CLIENT = {"name": "client", "description": "Client with limited access"}

DEFAULT_ROLES = [ROLE_ADMIN, ROLE_USER, ROLE_CLIENT]
```

### Permissions Structure

Each role has a JSON-based permissions object stored in the database.

```json
{
  "can_edit_workspace": true,
  "can_create_projects": true,
  "can_invite_users": true
}
```

---

## 🧱 Database Structure & Architecture

The system uses a **modular monolith** architecture with decoupled apps that share a common PostgreSQL database.

! [Database Schema](https://app.eraser.io/workspace/wvjKjAY77RE1k8DBA42p)

Each model belongs to a separate domain:
- **accounts/**: Custom user model with extended fields, email-based authentication.
- **workspace/**: Workspaces, members, roles, permissions.
- **project/**: Projects, project members, billing options, financial operations.

Future support planned for database sharding or microservice separation.

---

## 📁 Project Structure

```text
accounts/           # Authentication and user management
core/               # Project configuration and entrypoints
project/            # Project logic and billing
workspace/          # Workspaces and user roles
tools/              # Permissions and helpers
utils/              # Management commands
staticfiles/        # Static file collection
templates/emails/   # Email templates
test_db_data/       # Fixtures for testing
```

---

## 🔐 Role Usage Example

When a user joins a workspace, their actions are validated through their assigned role permissions using custom permission classes in `tools/permissions/`.

Example checks:
- Can the user invite others?
- Can the user edit a project?
- Can the user view financial reports?

---

## 📈 Scalability

Current setup uses a centralized database. In future, the plan includes:
- Sharded databases per module (accounts, billing, etc.)
- Microservices with individual DBs

---

## 🐳 Docker & Deployment

This project includes production-ready Docker and Docker Compose files.

See [INSTALL.md](INSTALL.md) for local and production setup instructions.