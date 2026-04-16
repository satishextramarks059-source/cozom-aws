from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


# Utility function to send OTP email
def send_otp_email(user, otp_code):
        subject = "COZOM - Your account verification (OTP) Code"

        username = getattr(user, 'username', '')

        # Plain-text fallback message
        plain_message = (
                f"Dear {username}\n\n"
                f"Your OTP code is {otp_code}. It will expire in 5 minutes.\n\n"
                "If you did not request this code, please ignore this email.\n\n"
                "Thanks,\nCOZOM Team"
        )

        # Render HTML template from templates/accounts/otp_email.html
        try:
                html_message = render_to_string('accounts/otp_email.html', {
                        'username': username,
                        'otp_code': otp_code,
                })
        except Exception:
                # fallback: simple inline HTML if template rendering fails
                html_message = f"<html><body><p>Dear {username},</p><p>Your OTP code is <strong>{otp_code}</strong>. It will expire in 5 minutes.</p><p>Thanks,<br/>COZOM Team</p></body></html>"

        # Ensure plain text fallback is present (strip HTML if needed)
        if not plain_message:
                plain_message = strip_tags(html_message)

        # Send email with both plain text and HTML parts
        send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message)