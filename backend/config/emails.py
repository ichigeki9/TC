import logging

from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_email(template, context, to):
    """
    Wysyła maila z szablonu templates/emails/<template>.txt — pierwsza linia to temat.
    Jeśli jest też <template>.html, mail ma ładną wersję HTML (tekst zostaje jako zapasowy).

    Błąd serwera poczty nie przerywa zakupu ani rejestracji: trafia do logów,
    a funkcja zwraca False.
    """
    subject, body = render_to_string(f'emails/{template}.txt', context).strip().split('\n', 1)
    try:
        html = render_to_string(f'emails/{template}.html', context)
    except TemplateDoesNotExist:
        html = None
    message = EmailMultiAlternatives(subject.strip(), body.strip() + '\n', None, to)
    if html:
        message.attach_alternative(html, 'text/html')
    try:
        message.send()
    except Exception:
        logger.exception('Nie udało się wysłać maila %s do %s', template, ', '.join(to))
        return False
    return True
