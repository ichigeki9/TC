from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Adres e-mail jest wymagany.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('display_name', 'Admin')
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Użytkownik logujący się e-mailem. Nazwa w rankingu to display_name."""

    class Gender(models.TextChoices):
        FEMALE = 'F', 'Kobieta'
        MALE = 'M', 'Mężczyzna'

    username = None
    email = models.EmailField('e-mail', unique=True)
    display_name = models.CharField('nazwa w rankingu', max_length=40)
    gender = models.CharField('płeć', max_length=1, choices=Gender.choices, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.display_name or self.email
