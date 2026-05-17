from django.conf import settings
from django.core.mail import send_mail
from django.core.signing import TimestampSigner


# Блок 1. Генерация token подтверждения email.
# Нужна, чтобы создать защищённую ссылку для подтверждения регистрации.
def generate_email_confirmation_token(user):
    signer = TimestampSigner()

    return signer.sign(str(user.id))


# Блок 2. Отправка письма подтверждения.
# В режиме разработки письмо выводится в консоль через console email backend.
def send_email_confirmation(user, request=None):
    token = generate_email_confirmation_token(user)
    confirm_url = settings.EMAIL_CONFIRMATION_URL.format(token=token)

    subject = 'Подтверждение регистрации MatchFlow'
    message = (
        f'Здравствуйте, {user.first_name or user.username}!\n\n'
        f'Для подтверждения регистрации перейдите по ссылке:\n'
        f'{confirm_url}\n\n'
        f'Ссылка действует 24 часа.'
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    return confirm_url
