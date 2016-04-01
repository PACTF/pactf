"""Commands that send email"""

from django.template.loader import render_to_string

from post_office import mail

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
    subject = render_to_string('ctflex/email/registration.subject.txt', context)

    mail.send(
        user.email,
        settings.DEFAULT_FROM_EMAIL,

        subject=subject,
        message=message,
    )
