from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

def send_invite_email(user, workspace):
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
            to=[user.email]
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()