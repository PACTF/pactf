"""Commands that send email"""

from django.core import mail
from django.template.loader import render_to_string

from ctflex import settings


def confirm_registration(user):
    """Confirm registration with user"""

    # Don’t do anything if the email host isn’t defined
    if not settings.EMAIL_HOST:
        return

    context = {
        'user': user,
        'support_email': settings.SUPPORT_EMAIL,
        'sitename': settings.SITENAME,
    }

    message = render_to_string('ctflex/email/registration.txt', context)
    # html_message = render_to_string('ctflex/auth/confirm_email.html', context)
    subject = render_to_string('ctflex/email/registration.subject.txt', context)

    mail.send_mail(
        subject=subject,
        message=message,

        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
