from django.core import mail
from django.template.loader import render_to_string

from ctflex import settings

def confirm(user, team, competitor):
    context = {'user' : user, 'team' : team, 'competitor' : competitor}
    html_message = render_to_string('ctflex/auth/confirm.html', context)
    # This is actually an extremely dirty hack but I can't thnk of a better way to do this.
    plaintext = render_to_string('ctflex/text/confirm.txt', context)
    mail.send_mail(
        subject='confirmation', message=plaintext,
        from_email=settings.EMAIL_HOST_USER, recipient_list=[user.email],
        # TODO: Catch this
        fail_silently=False,
        html_message=html_message
    )
