from rest_framework import serializers
from workspace.models import Workspace, WorkspaceMembership, WorkspaceRole
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import CustomUser
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class WorkspaceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Workspace
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated")

        return Workspace.objects.create(owner=request.user, **validated_data)
    

class WorkspaceMembershipSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    role_id = serializers.IntegerField(write_only=True, required=False)
    role = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = WorkspaceMembership
        fields = ['email', 'role_id', 'role', 'joined_at']
        read_only_fields = ['joined_at']

    def validate(self, data):
        """
        We check that the user is not the owner or has not already been added to the workspace.
        """
        email = data.get('email')
        workspace = self.context.get('workspace')
        
        if not workspace:
            raise serializers.ValidationError({"workspace": "Workspace is required."})

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            user = None  # We'll send a letter later

        if user:
            if user == workspace.owner:
                raise serializers.ValidationError("Owner cannot be added as a member.")
            if WorkspaceMembership.objects.filter(workspace=workspace, user=user).exists():
                raise serializers.ValidationError("User is already a member.")

        role_id = data.get('role_id')
        role_name = data.get('role')
        role = None

        if role_id:
            try:
                role = WorkspaceRole.objects.get(id=role_id, workspace=workspace)
            except WorkspaceRole.DoesNotExist:
                raise serializers.ValidationError({"role_id": "Role does not exist in this workspace."})

        elif role_name:
            try:
                role = WorkspaceRole.objects.get(name=role_name, workspace=workspace)
            except WorkspaceRole.DoesNotExist:
                raise serializers.ValidationError({"role": f"Role '{role_name}' does not exist in this workspace."})

        data['user'] = user
        data['role'] = role
        return data

    def create(self, validated_data):
        email = validated_data.pop('email')
        workspace = self.context.get('workspace')
        role = validated_data.pop('role', None)

        user = validated_data.get('user')

        if not user:
            user = CustomUser.objects.create(email=email, is_active=False)

            token = RefreshToken.for_user(user).access_token
            reset_link = f"{settings.FRONTEND_URL}/accounts/set-password/?token={token}"

            # from django.core.mail import send_mail
            # send_mail(
            #     subject="Invitation to workspace",
            #     message=f"You have been invited to workspace {workspace.name}. Set a password using the link: {reset_link}",
            #     from_email="snagadevteam@gmail.com",
            #     recipient_list=[email],
            #     fail_silently=False,
            # )

            html_content = render_to_string("emails/set_password_email.html", {
                "workspace_name": workspace.name,
                "reset_link": reset_link
            })

            email_message = EmailMultiAlternatives(
                subject="Set password.",
                body=f"Follow the link to set a password: {reset_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            email_message.attach_alternative(html_content, "text/html")
            email_message.send()

        membership = WorkspaceMembership.objects.create(user=user, workspace=workspace, role=role)
        return membership