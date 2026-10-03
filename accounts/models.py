from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Every actor of the hub: student, lecturer or platform admin.

    NIM/NIP are optional, non-primary columns kept separate on purpose so they
    map cleanly onto the academic system later (docs/adr/002).
    """

    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        LECTURER = "lecturer", "Lecturer"
        ADMIN = "admin", "Admin"

    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    # NIM
    student_id_number = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        unique=True,
    )
    # NIP
    lecturer_id_number = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        unique=True,
    )
    study_program = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        # createsuperuser never sets `role`; keep superusers consistent so
        # role-based checks don't lock Django's own superuser out.
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"
