from django.db import models

from accounts.models import User, validate_hex_color
from workspace.models import Workspace


class Project(models.Model):
    """
    Represents a project within a specific workspace.

    A project includes metadata such as name, description, visibility,
    billing status, and visual representation (emoji, background, image).
    Each project is tied to a workspace and can be public or private,
    active or archived, and billable or not.

    Fields:
        name (str): The human-readable name of the project.
        key (str): A short unique identifier for the project (e.g., abbreviation).
        description (str): Optional detailed description of the project.
        workspace (Workspace): The workspace to which the project belongs.
        is_public (bool): Indicates whether the project is visible to all workspace members.
        is_billable (bool): Indicates whether time tracked in this project is billable.
        is_active (bool): Indicates whether the project is currently active.
        avatar_background (str): HEX color code for the avatar background.
        avatar_emoji (str): Emoji used as a symbolic avatar for the project.
        avatar_image (Image): Optional image used as the project’s avatar.
        created_at (datetime): Timestamp when the project was created.
        updated_at (datetime): Timestamp when the project was last updated.
    """

    name = models.CharField(verbose_name="Name", max_length=150)
    key = models.CharField(verbose_name="Key", max_length=10)
    description = models.TextField(verbose_name="Description", blank=True, null=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="project_workspace", verbose_name="Workspace")
    is_public = models.BooleanField(default=True, verbose_name="Is Public")
    is_billable = models.BooleanField(default=True, verbose_name="Is Billable")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    avatar_background = models.CharField(
        max_length=7,
        verbose_name="Avatar Background",
        default="#ffffff", 
        validators=[validate_hex_color], 
        null=True,
        blank=True
    )
    avatar_emoji = models.CharField(max_length=3, verbose_name="Avatar Emoji", default="🚀")
    avatar_image = models.ImageField(
        upload_to="project/", 
        verbose_name="Avatar Image",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date of create")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date of update")

    def __str__(self) -> str:
        return self.key


class ProjectMember(models.Model):
    """
    Represents a user's membership in a specific project.

    Each record links a user to a project, with metadata about their
    membership status and the date they joined. One user can be part
    of many projects, but only once per project.

    Fields:
        user (User): The user who is a member of the project.
        project (Project): The project in which the user is a member.
        joined_at (datetime): Timestamp when the user was added to the project.
        is_active (bool): Indicates whether the user's membership is currently active.
        created_at (datetime): Timestamp when the project was created.
        updated_at (datetime): Timestamp when the project was last updated.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="project_member", verbose_name="User")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="members", verbose_name="Project")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="Date of joined")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date of create")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date of update")

    class Meta:
        unique_together = ('user', 'project')
        verbose_name = "Project Member"
        verbose_name_plural = "Project Members"


    def __str__(self) -> str:
        return f"{self.user.email} in {self.project.name}"


class ProjectBilling(models.Model):
    """
    Represents billing configuration for a specific project.

    Defines how billing is calculated (e.g., hourly, fixed),
    the spending or usage limit, and tracks creation and update timestamps.

    Fields:
        project (Project): The project associated with this billing rule.
        type (str): The billing method (e.g., hourly, fixed, subscription).
        limit (float): Spending or usage limit for this billing configuration.
        created_at (datetime): Timestamp when the billing record was created.
        updated_at (datetime): Timestamp when the billing record was last updated.
    """

    class BillingType(models.TextChoices):
        HOURLY = 'hourly', 'Hourly'
        FIXED = 'fixed', 'Fixed Price'
        SUBSCRIPTION = 'subscription', 'Subscription'
        PER_TASK = 'per_task', 'Per Task'
        NON_BILLABLE = 'non_billable', 'Non-Billable'


    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="billing", verbose_name="Project")
    type = models.CharField(max_length=20, choices=BillingType.choices, default=BillingType.FIXED, verbose_name="Type")
    limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Billing Limit",
        help_text="Maximum budget or spending limit. Use 0.00 if unlimited."
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date of create")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date of update")

    def __str__(self) -> str:
        return f"{self.project.name} – {self.get_type_display()}"


class ProjectQuote(models.Model):
    """
    Represents a financial quote (billing entry) associated with a project billing setup.

    Each quote can represent an invoice, payment, or budget item depending on the type.
    It includes metadata such as the amount, type of quote (hourly, fixed, etc.), type
    of operation (e.g. deposit, withdrawal), and an optional proof file (receipt, invoice).

    Fields:
        description (str): Optional description of the quote.
        project_billing (ProjectBilling): Related billing configuration.
        quote_type (str): How this quote should be interpreted (e.g., hourly, fixed).
        operation_type (str): Nature of the transaction (deposit, withdrawal, etc.).
        amount (float): The transaction amount (positive or negative).
        proof (File): Optional uploaded file as proof of transaction.
        created_at (datetime): Timestamp of quote creation.
        updated_at (datetime): Timestamp of last update.
    """

    class QuoteType(models.TextChoices):
        DEPOSIT = 'deposit', 'Deposit'
        WITHDRAWAL = 'withdrawal', 'Withdrawal'
        INVOICE = 'invoice', 'Invoice Issued'
        REFUND = 'refund', 'Refund'

    description = models.TextField(verbose_name="Description", blank=True, null=True)
    project_billing = models.ForeignKey(ProjectBilling, on_delete=models.CASCADE, related_name="quotes", verbose_name="Project billing")
    quote_type = models.CharField(max_length=20, choices=QuoteType.choices, default=QuoteType.INVOICE, verbose_name="Quote type")
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Transaction Amount",
        help_text="Use negative values for withdrawals if needed"
    )
    proof = models.FileField(
        upload_to="billing/proofs/",
        verbose_name="Proof of Transaction",
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date of create")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date of update")

    def __str__(self) -> str:
        return f"{self.operation_type.title()} – {self.amount:.2f} ({self.quote_type})"
