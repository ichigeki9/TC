import logging

from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_email(template, context, to):
    """
    Wysyła maila z szablonu templates/emails/<template>.txt — pierwsza linia to temat.

    Błąd serwera poczty nie przerywa zakupu ani rejestracji: trafia do logów,
    a funkcja zwraca False.
    """
    subject, body = render_to_string(f'emails/{template}.txt', context).strip().split('\n', 1)
    try:
        send_mail(subject.strip(), body.strip() + '\n', None, to)
    except Exception:
        logger.exception('Nie udało się wysłać maila %s do %s', template, ', '.join(to))
        return False
    return True
