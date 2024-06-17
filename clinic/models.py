import uuid
from datetime import time

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from python_usernames import is_safe_username


class UserType(models.IntegerChoices):
    """UserType enum for defining the type of user."""

    PATIENT = 0, 'Patient'
    DOCTOR = 1, 'Doctor'
    ADMIN = 2, 'Admin'
    SUPERUSER = 3, 'Superuser'


class AdminUserType(models.IntegerChoices):
    """AdminUserType enum for defining the type of admin user."""

    PATIENT = 0, 'Patient'
    DOCTOR = 1, 'Doctor'


class VisitStatus(models.TextChoices):
    """VisitStatus enum for defining the status of a visit."""

    VISITED = 'visited', 'Visited'
    MISSED = 'missed', 'Missed'
    CANCELLED = 'cancelled', 'Cancelled'
    ACTIVE = 'active', 'Active'
    SCHEDULED = 'scheduled', 'Scheduled'


class WeekDays(models.IntegerChoices):
    """WeekDays enum for defining the days of the week."""

    MONDAY = 0, 'Понедельник'
    TUESDAY = 1, 'Вторник'
    WEDNESDAY = 2, 'Среда'
    THURSDAY = 3, 'Четверг'
    FRIDAY = 4, 'Пятница'
    SATURDAY = 5, 'Суббота'
    SUNDAY = 6, 'Воскресенье'


class UUIDMixin(models.Model):
    """UUIDMixin model for providing a UUID field."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    """UserManager model for managing User model."""

    def create_user(
            self,
            username,
            fullname,
            email=None,
            phone=None,
            user_level=UserType.PATIENT,
            password=None,
            **extra_fields
            ):
        """Create a new user.

        Args:
            username (str): The username of the user.
            fullname (str): The full name of the user.
            email (str, optional): The email of the user. Defaults to None.
            phone (str, optional): The phone number of the user. Defaults to None.
            user_level (UserType, optional): The level of the user. Defaults to UserType.PATIENT.
            password (str, optional): The password of the user. Defaults to None.
            **extra_fields: Additional fields.

        Returns:
            User: The created user.
        """
        if not username:
            raise ValueError('The Username field must be set')
        if not password:
            raise ValueError('The password field must be set')
        if not is_safe_username(username, max_length=15):
            raise ValueError('The Username is not safe')
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        email = self.normalize_email(email)
        user = self.model(
            username=username,
            fullname=fullname,
            email=email,
            phone=phone,
            user_level=user_level,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
            self,
            username,
            fullname,
            email=None,
            phone=None,
            password=None,
            **extra_fields
            ):
        """Create a new superuser.

        Args:
            username (str): The username of the superuser.
            fullname (str): The full name of the superuser.
            email (str, optional): The email of the superuser. Defaults to None.
            phone (str, optional): The phone number of the superuser. Defaults to None.
            password (str, optional): The password of the superuser. Defaults to None.
            **extra_fields: Additional fields.

        Returns:
            User: The created superuser.
        """

        extra_fields.setdefault('user_level', UserType.SUPERUSER)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(
            username=username,
            fullname=fullname,
            email=email,
            phone=phone,
            password=password,
            **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin, UUIDMixin):
    """User model for representing a user."""

    username = models.CharField(max_length=15, unique=True)
    user_level = models.SmallIntegerField(choices=UserType.choices, default=UserType.PATIENT)
    created_at = models.DateTimeField(auto_now_add=True)
    fullname = models.CharField(max_length=50)
    email = models.EmailField(max_length=64, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    specialty = models.CharField(max_length=50, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['fullname', 'user_level']

    objects = UserManager()

    def __str__(self):
        """Return a string representation of the user.

        Returns:
            str: A string representation of the user.
        """
        return f'{self.fullname} ({self.get_user_level_display()})'

    def save(self, *args, **kwargs):
        """Save the user.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        if not is_safe_username(self.username):
            raise ValueError('The Username is not safe')
        super().save(*args, **kwargs)

    def save_model(self, request, obj, form, change, **kwargs):
        """Save the model.

        Args:
            request (HttpRequest): The request object.
            obj (Model): The object to be saved.
            form (ModelForm): The form to be saved.
            change (bool): Whether the object is being changed or created.
            **kwargs: Additional keyword arguments.
        """
        if 'password' in form.changed_data:
            obj.set_password(form.cleaned_data['password'])
        if 'username' in form.changed_data:
            if not is_safe_username(self.username):
                raise ValueError('The Username is not safe')
        super().save_model(request, obj, form, change)


class Visit(models.Model):
    """Visit model for representing a visit."""
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_visits')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_visits')
    date = models.DateField()
    start = models.TimeField()
    end = models.TimeField()
    status = models.CharField(max_length=20,
                              choices=VisitStatus.choices,
                              default=VisitStatus.ACTIVE)
    description = models.TextField(blank=True)

    def __str__(self):
        """Return a string representation of the visit.

        Returns:
            str: A string representation of the visit.
        """
        return f'{self.doctor} - {self.patient} on {self.date} \
            from {self.start.strftime("%H:%M")} to {self.end.strftime("%H:%M")}'


class Schedule(models.Model):
    """Schedule model for representing a schedule."""
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules')
    start = models.TimeField()  # in 15-minute intervals from 00:00
    end = models.TimeField()  # in 15-minute intervals from 00:00
    day_of_week = models.SmallIntegerField(choices=WeekDays.choices, null=False, blank=False)

    def clean(self):
        """Validate the schedule.

        Raises:
            ValidationError: If the schedule is not valid.
        """
        # print(self.start, self.end)
        if self.start is None and self.end is None:
            raise ValidationError('Start and end times are required.')
        if self.start < time(0, 0) or self.end <= time(0, 0):
            raise ValidationError("Start and end times must be positive.")
        if self.doctor.user_level != UserType.DOCTOR:
            raise ValidationError("The assigned doctor must have the Doctor user level.")
        if not self.doctor.is_active:
            raise ValidationError("The doctor is not active.")
        if self.start >= self.end:
            raise ValidationError("Start time must be before end time.")

        super().clean()

    def get_start_time(self):
        """Get the end time of the schedule.

        Returns:
            str: The end time of the schedule.
        """
        return self.start.strftime('%H:%M')

    def get_end_time(self):
        """Get the start time of the schedule.

        Returns:
            str: The start time of the schedule.
        """
        return self.end.strftime('%H:%M')

    def __str__(self):
        """Return a string representation of the schedule.

        Returns:
            str: A string representation of the schedule.
        """
        return f'{self.doctor} on {self.day_of_week} from {self.start.strftime("%H:%M")} \
                to {self.end.strftime("%H:%M")}'


class Diagnosis(UUIDMixin):
    """Diagnosis model for representing a diagnosis."""
    description = models.CharField(null=True, blank=True, max_length=500)
    patient = models.ForeignKey(User,
                                on_delete=models.DO_NOTHING,
                                related_name='diagnoses_as_patient')
    doctor = models.ForeignKey(User,
                               on_delete=models.DO_NOTHING,
                               related_name='diagnoses_as_doctor')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation of the diagnosis.

        Returns:
            str: A string representation of the diagnosis.
        """
        return f'Diagnosis for {self.patient.fullname} by {self.doctor.fullname}'
