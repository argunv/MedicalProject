import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from python_usernames import is_safe_username
from datetime import time, timedelta, datetime


class UserType(models.IntegerChoices):
    PATIENT = 0, 'Patient'
    DOCTOR = 1, 'Doctor'
    ADMIN = 2, 'Admin'
    SUPERUSER = 3, 'Superuser'

class AdminUserType(models.IntegerChoices): # Choises for Admin
    PATIENT = 0, 'Patient'
    DOCTOR = 1, 'Doctor'

class VisitStatus(models.TextChoices):
    VISITED = 'visited', 'Visited'
    MISSED = 'missed', 'Missed'
    CANCELLED = 'cancelled', 'Cancelled'
    ACTIVE = 'active', 'Active'
    SCHEDULED = 'scheduled', 'Scheduled'

class WeekDays(models.IntegerChoices):
    WEDNESDAY = 0, 'Wednesday'
    THURSDAY = 1, 'Thursday'
    FRIDAY = 2, 'Friday'
    SATURDAY = 3, 'Saturday'
    SUNDAY = 4, 'Sunday'
    MONDAY = 5, 'Monday'
    TUESDAY = 6, 'Tuesday'

class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

class UserManager(BaseUserManager):
    def create_user(self, username, fullname, email=None, phone=None, user_level=UserType.PATIENT, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        if not password:
            raise ValueError('The password field must be set')
        if not is_safe_username(username, max_length=15):
            raise ValueError('The Username is not safe')
        
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

    def create_superuser(self, username, fullname, email=None, phone=None, password=None, **extra_fields):
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
        return f'{self.fullname} ({self.get_user_level_display()})'

    def save(self, *args, **kwargs):
        if not is_safe_username(self.username):
            raise ValueError('The Username is not safe')
        super().save(*args, **kwargs)

    def save_model(self, request, obj, form, change, **kwargs):
        if 'password' in form.changed_data:
            obj.set_password(form.cleaned_data['password'])
        if 'username' in form.changed_data:
            if not is_safe_username(self.username):
                raise ValueError('The Username is not safe')
        super().save_model(request, obj, form, change)

class Visit(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_visits')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_visits')
    date = models.DateField()
    start = models.IntegerField()
    end = models.IntegerField()
    status = models.CharField(max_length=20, choices=VisitStatus.choices, default=VisitStatus.SCHEDULED)
    description = models.TextField(blank=True)

    def __str__(self):
        return f'{self.doctor} - {self.patient} on {self.date} from {self.start*15} to {self.end*15} minutes'

class Schedule(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules')
    start = models.PositiveIntegerField()  # in 15-minute intervals from 00:00
    end = models.PositiveIntegerField()  # in 15-minute intervals from 00:00
    day_of_week = models.SmallIntegerField(choices=WeekDays.choices, null=False, blank=False)

    def __str__(self):
        return f'{self.doctor} on {self.day_of_week} from {self.start*15} to {self.end*15} minutes'

    def clean(self):
        # print(self.start, self.end)
        if self.start is not None and self.end is not None:
            raise ValidationError('Start and end times are required.')
        if self.start < 0 or self.end <= 0:
            raise ValidationError("Start and end times must be positive.")
        if self.doctor.user_level != UserType.DOCTOR:
            raise ValidationError("The assigned doctor must have the Doctor user level.")
        if not self.doctor.is_active:
            raise ValidationError("The doctor is not active.")
        if self.start >= self.end:
            raise ValidationError("Start time must be before end time.")
        if self.start < 0 or self.end > 96:
            raise ValidationError("Start and end times must be within the range of 0 to 96.")

        super().clean()

    def get_start_time(self):
        return (datetime.combine(datetime.today(), time(0)) + timedelta(minutes=15 * self.start)).strftime('%H:%M')

    def get_end_time(self):
        return (datetime.combine(datetime.today(), time(0)) + timedelta(minutes=15 * self.end)).strftime('%H:%M')

    def __str__(self):
        return f'Schedule for {self.doctor.fullname} on {self.get_day_of_week_display()} from {self.get_start_time()} to {self.get_end_time()}'

class Diagnosis(UUIDMixin):
    description = models.CharField(null=True, blank=True, max_length=500)
    patient = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='diagnoses_as_patient')
    doctor = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='diagnoses_as_doctor')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Diagnosis for {self.patient.fullname} by {self.doctor.fullname}'
