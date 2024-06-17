from datetime import datetime
from django import forms
from django.contrib.auth.forms import BaseUserCreationForm
from django.core.exceptions import PermissionDenied, ValidationError
from django.forms.widgets import HiddenInput
from python_usernames import is_safe_username

from .models import (
    User,
    Visit,
    Schedule,
    Diagnosis,
    UserType,
    AdminUserType,
    VisitStatus,
)

from .config import ERROR_MESSAGES, WORK_DAY_DURATION_LIMIT, STATUS_ACTIVE, WEEKDAYS_CHOICES, START_END_ATTRS


def user_form_viewer(user_level: UserType) -> type[forms.ModelForm]:
    """Returns the appropriate user form based on the user level.

    Args:
        user_level: The user level.

    Returns:
        The user form class.
    """
    if user_level == UserType.PATIENT:
        return PatientUserForm
    elif user_level == UserType.DOCTOR:
        return DoctorUserForm
    elif user_level == UserType.ADMIN:
        return AdminUserForm
    elif user_level == UserType.SUPERUSER:
        return SuperUserForm
    else:
        raise PermissionDenied(ERROR_MESSAGES['invalid_user_level'])


def register_user_form_viewer(user_level: UserType) -> type[forms.ModelForm]:
    """
    Returns the appropriate registration form based on the user level.

    Args:
        user_level: The user level.

    Returns:
        The registration form class.
    """
    if user_level == UserType.SUPERUSER:
        return SuperUserRegistrationForm
    elif user_level == UserType.ADMIN:
        return AdminUserRegistrationForm
    elif user_level == UserType.PATIENT:
        return PatientRegistrationForm
    elif user_level == UserType.DOCTOR:
        return DoctorRegistrationForm
    else:
        raise PermissionDenied(ERROR_MESSAGES['invalid_user_level'])


class UserForm(forms.ModelForm):
    """
    Base form for user-related forms.
    """

    def clean_fullname(self) -> str:
        """
        Validates the fullname field.

        Returns:
            The cleaned fullname.
        """
        fullname = self.cleaned_data.get('fullname')
        if not fullname:
            raise ValidationError(ERROR_MESSAGES['empty_fullname'])
        if any(char.isdigit() for char in fullname):
            raise ValidationError(ERROR_MESSAGES['contains_numbers'])
        joined_fullname = ' '.join([word.strip() for word in fullname.split()])
        fullname_length = len(joined_fullname.split())
        if fullname_length != 2:
            raise ValidationError(ERROR_MESSAGES['invalid_fullname'])
        return joined_fullname

    def clean_date_of_birth(self) -> datetime.date:
        """
        Validates the date_of_birth field.

        Returns:
            The cleaned date_of_birth.
        """
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > datetime.date.today():
            raise ValidationError(ERROR_MESSAGES['future_dob'])
        return dob

    def clean_phone(self) -> str:
        """
        Validates the phone field.

        Returns:
            The cleaned phone.
        """
        phone = self.cleaned_data.get('phone')
        if not phone:
            return
        if phone and not phone.isdigit():
            raise ValidationError(ERROR_MESSAGES['invalid_phone'])
        return phone.strip()

    def clean_email(self) -> str:
        """
        Validates the email field.

        Returns:
            The cleaned email.
        """
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError(ERROR_MESSAGES['empty_email'])
        return email.strip()

    def clean_username(self) -> str:
        """
        Validates the username field.

        Returns:
            The cleaned username.
        """
        username = self.cleaned_data.get('username')
        if not is_safe_username(username):
            raise ValidationError(ERROR_MESSAGES['invalid_username'])
        return username

    def clean_user_level(self) -> int:
        """
        Validates the user_level field.

        Returns:
            The cleaned user_level.
        """
        user_level = self.cleaned_data.get('user_level', self.instance.user_level)
        specialty = self.data.get('specialty')
        if user_level not in UserType:
            raise ValidationError(ERROR_MESSAGES['invalid_user_level'])
        if user_level != UserType.DOCTOR and specialty:
            raise ValidationError(ERROR_MESSAGES['invalid_specialty'])
        return user_level

    def clean_specialty(self) -> str:
        """
        Validates the specialty field.

        Returns:
            The cleaned specialty.
        """
        specialty = self.cleaned_data.get('specialty')
        user_level = self.data.get('user_level', self.instance.user_level)

        if user_level != UserType.DOCTOR and specialty:
            raise ValidationError(ERROR_MESSAGES['invalid_specialty'])

        if user_level == UserType.DOCTOR:
            if not specialty:
                raise ValidationError(ERROR_MESSAGES['required_specialty'])
            if not specialty.isalpha():
                raise ValidationError(ERROR_MESSAGES['invalid_specialty_letters'])
        return specialty


class PatientUserForm(UserForm):
    """
    Form for creating/editing patient users.
    """

    class Meta:
        model = User
        fields = ['username', 'fullname', 'email', 'phone']


class DoctorUserForm(UserForm):
    """
    Form for creating/editing doctor users.
    """

    class Meta:
        model = User
        fields = ['username', 'fullname', 'email', 'phone', 'specialty']


class AdminUserForm(UserForm):
    """
    Form for creating/editing admin users.
    """

    class Meta:
        model = User
        fields = ['username', 'fullname', 'email', 'phone', 'specialty', 'is_active']


class SuperUserForm(UserForm):
    """
    Form for creating/editing superuser users.
    """

    is_staff = forms.BooleanField(required=False, widget=HiddenInput(), initial=False)
    is_superuser = forms.BooleanField(required=False, widget=HiddenInput(), initial=False)

    class Meta:
        model = User
        fields = ['username',
                  'fullname',
                  'email',
                  'phone',
                  'specialty',
                  'user_level',
                  'is_active',
                  'is_superuser',
                  'is_staff']

    def clean(self):
        """
        Cleans the form data.

        Returns:
            The cleaned data.
        """
        cleaned_data = super().clean()
        user_level = cleaned_data.get('user_level')
        if user_level in [UserType.PATIENT, UserType.DOCTOR]:
            cleaned_data['is_staff'] = False
            cleaned_data['is_superuser'] = False
        return cleaned_data


class UserRegistrationForm(BaseUserCreationForm, UserForm):
    """
    Base form for user registration.
    """

    def clean_username(self) -> str:
        """
        Validates the username field.

        Returns:
            The cleaned username.
        """
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError(ERROR_MESSAGES['invalid_username'])
        return username

    def clean_email(self) -> str:
        """
        Validates the email field.

        Returns:
            The cleaned email.
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(ERROR_MESSAGES['invalid_email'])
        return email

    def clean_phone(self) -> str:
        """
        Validates the phone field.

        Returns:
            The cleaned phone.
        """
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise ValidationError(ERROR_MESSAGES['invalid_phone'])
        if not phone.isdigit():
            raise ValidationError(ERROR_MESSAGES['invalid_phone'])
        if User.objects.filter(phone=phone).exists():
            raise ValidationError(ERROR_MESSAGES['invalid_phone'])
        return phone


class SuperUserRegistrationForm(UserRegistrationForm):
    """
    Form for creating superuser users.
    """

    class Meta:
        model = User
        fields = ['username', 'fullname', 'email', 'phone', 'user_level', 'is_active', 'password1', 'password2']

    def save(self, commit=True):
        """
        Saves the form data.

        Args:
            commit: Whether to save the data to the database.

        Returns:
            The saved user object.
        """
        user = super().save(commit=False)
        # Save the password if set
        if 'new_password1' in self.cleaned_data and self.cleaned_data['new_password1']:
            user.set_password(self.cleaned_data['new_password1'])
        if commit:
            user.save()
        return user


class AdminUserRegistrationForm(UserRegistrationForm):
    """
    Form for creating admin users.
    """

    user_level = forms.TypedChoiceField(coerce=int, choices=AdminUserType.choices, initial=AdminUserType.PATIENT)

    class Meta:
        model = User
        fields = ['username', 'fullname', 'email', 'phone', 'is_active', 'password1', 'password2']

    def save(self, commit=True):
        """
        Saves the form data.

        Args:
            commit: Whether to save the data to the database.

        Returns:
            The saved user object.
        """
        user = super().save(commit=False)
        # Save the password if set
        if 'new_password1' in self.cleaned_data and self.cleaned_data['new_password1']:
            user.set_password(self.cleaned_data['new_password1'])
        if commit:
            user.save()
        return user


class PatientRegistrationForm(UserRegistrationForm):
    """
    Form for creating patient users.
    """

    class Meta:
        model = User
        fields = ['username', 'fullname', 'email', 'phone', 'user_level']


class DoctorRegistrationForm(UserRegistrationForm):
    """
    Form for creating doctor users.
    """

    class Meta:
        model = User
        fields = ['username', 'fullname', 'email', 'phone', 'user_level', 'specialty']
        required_fields = ['username', 'fullname', 'email', 'phone', 'user_level', 'specialty']


class VisitForm(forms.ModelForm):
    """
    Base form for creating/editing visits.
    """
    start = forms.TimeField(widget=forms.TimeInput(format='%H:%M', attrs=START_END_ATTRS))
    end = forms.TimeField(widget=forms.TimeInput(format='%H:%M', attrs=START_END_ATTRS))
    date = forms.DateField(widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))

    def clean(self, patient: User = None,
              doctor: User = None,
              date: datetime.date = None):
        """Cleans the form data.

        Args:
            patient: The patient user.
            doctor: The doctor user.
            date: The visit date.

        Returns:
            The cleaned data.
        """
        cleaned_data = super().clean()
        if not patient or not doctor:
            doctor = cleaned_data.get('doctor')
            patient = cleaned_data.get('patient')
        date = cleaned_data.get('date')
        start = cleaned_data.get('start')
        end = cleaned_data.get('end')
        status = cleaned_data.get('status')

        if not doctor or not patient:
            raise ValidationError(ERROR_MESSAGES['required_doctor_patient'])
        if doctor == patient:
            raise ValidationError(ERROR_MESSAGES['doctor_self_visit'])
        if doctor.user_level != UserType.DOCTOR:
            raise ValidationError(ERROR_MESSAGES['invalid_user_level'])
        if patient.user_level != UserType.PATIENT:
            raise ValidationError(ERROR_MESSAGES['invalid_user_level'])
        if not doctor.is_active:
            raise ValidationError(ERROR_MESSAGES['inactive_doctor'])
        if start >= end:
            raise ValidationError(ERROR_MESSAGES['invalid_start_end_time'])
        if not date:
            raise ValidationError(ERROR_MESSAGES['invalid_time_format'])
        if (
            datetime.combine(datetime.min, end)
            - datetime.combine(datetime.min, start)
        ).total_seconds() > WORK_DAY_DURATION_LIMIT:
            raise ValidationError(ERROR_MESSAGES['exceeded_work_day_duration'])
        if start.minute % 15 != 0 or end.minute % 15 != 0:
            raise ValidationError(ERROR_MESSAGES['invalid_time_increment'])

        overlapping_visits = Visit.objects.filter(
            doctor=doctor,
            date=date,
            start__lt=end,
            end__gt=start
        ).exclude(id=self.instance.id)

        if overlapping_visits.exists():
            other_patient_visits = Visit.objects.filter(
                doctor=doctor,
                date=date,
                start__lt=end,
                end__gt=start,
                patient=patient
            ).exclude(id=self.instance.id)
            if other_patient_visits.exists():
                raise ValidationError(ERROR_MESSAGES['overlapping_visit'])

        # Check for doctor's schedule
        day_of_week = date.weekday()
        schedule = Schedule.objects.filter(
            doctor=doctor,
            day_of_week=day_of_week,
            start__lte=start,
            end__gte=end
        )
        if not schedule.exists():
            raise ValidationError(ERROR_MESSAGES['outside_schedule'])

        current_datetime = datetime.now()
        visit_datetime = datetime.combine(date, start)

        if visit_datetime > current_datetime and status in [VisitStatus.MISSED, VisitStatus.VISITED]:
            raise ValidationError(ERROR_MESSAGES['invalid_visit_status'])
        if visit_datetime <= current_datetime and status == VisitStatus.SCHEDULED:
            raise ValidationError(ERROR_MESSAGES['invalid_past_visit_status'])

        return cleaned_data


class VisitCreationForm(VisitForm):
    """
    Form for creating visits.
    """
    class Meta:
        model = Visit
        fields = ['date', 'start', 'end', 'description']
        required_fields = ['date', 'start', 'end']

    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None)
        patient = kwargs.pop('patient', None)
        super().__init__(*args, **kwargs)

        if doctor:
            self.initial['doctor'] = doctor
        if patient:
            self.initial['patient'] = patient

    def clean(self):
        cleaned_data = super().clean(doctor=self.initial['doctor'],
                                     patient=self.initial['patient'])
        cleaned_data['status'] = STATUS_ACTIVE
        return cleaned_data


class VisitViewForm(VisitForm):
    """
    Form for viewing visits.
    """
    class Meta:
        model = Visit
        fields = ['date', 'start', 'end', 'description']
        required_fields = ['date', 'start', 'end', 'status']

    def __init__(self, *args, **kwargs):
        # Убедитесь, что instance передан правильно
        visit = kwargs.get('instance', None)
        self.doctor = visit.doctor if visit else None
        self.patient = visit.patient if visit else None
        self.date = visit.date if visit else None
        super().__init__(*args, **kwargs)
        # Установка начальных значений полей
        if visit:
            self.fields['date'].value = visit.date.strftime('%Y-%m-%d')
            self.fields['start'].initial = visit.start
            self.fields['end'].initial = visit.end
            self.fields['description'].initial = visit.description

    def clean(self):
        cleaned_data = super().clean()
        # Дополнительная валидация, если необходимо
        if not cleaned_data.get('date'):
            raise ValidationError('Date is required')
        if not cleaned_data.get('start'):
            raise ValidationError('Start time is required')
        if not cleaned_data.get('end'):
            raise ValidationError('End time is required')
        return cleaned_data

    def save(self, commit=True):
        visit = super().save(commit=False)
        # Установка дополнительных атрибутов
        visit.doctor = self.doctor
        visit.patient = self.patient
        visit.date = self.cleaned_data['date']
        visit.start = self.cleaned_data['start']
        visit.end = self.cleaned_data['end']
        visit.description = self.cleaned_data['description']

        if commit:
            visit.save()
        return visit


class AdminVisitViewForm(VisitForm):
    """
    Form for viewing visits (admin).
    """
    class Meta:
        model = Visit
        fields = ['doctor', 'patient', 'date', 'start', 'end', 'status', 'description']
        required_fields = ['doctor', 'patient', 'date', 'start', 'end', 'status']


class AdminVisitCreationForm(VisitForm):
    """
    Form for creating visits (admin).
    """
    class Meta:
        model = Visit
        fields = ['doctor', 'patient', 'date', 'start', 'end', 'description']
        required_fields = ['doctor', 'patient', 'date', 'start', 'end']


class DiagnosisForm(forms.ModelForm):
    """
    Form for creating/editing diagnoses.
    """
    class Meta:
        model = Diagnosis
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        patient = cleaned_data.get('patient')
        description = cleaned_data.get('description')
        if not doctor or not patient:
            raise ValidationError(ERROR_MESSAGES['doctor_patient_required'])
        if doctor.user_level != UserType.DOCTOR:
            raise ValidationError(ERROR_MESSAGES['doctor_level'])
        if patient.user_level != UserType.PATIENT:
            raise ValidationError(ERROR_MESSAGES['patient_level'])
        if not doctor.is_active:
            raise ValidationError(ERROR_MESSAGES['doctor_inactive'])
        if not description:
            raise ValidationError(ERROR_MESSAGES['description_required'])
        if len(description) < 10:
            raise ValidationError(ERROR_MESSAGES['description_detailed'])

        return cleaned_data


class ScheduleForm(forms.ModelForm):
    """
    Base form for creating/editing schedules.
    """
    def clean(self):
        cleaned_data = super().clean()
        doctor = self.cleaned_data.get('doctor')
        start = cleaned_data.get('start')
        end = cleaned_data.get('end')
        day_of_week = cleaned_data.get('day_of_week')

        if not doctor:
            raise ValidationError(ERROR_MESSAGES['doctor_assigned'])
        if not doctor.is_active:
            raise ValidationError(ERROR_MESSAGES['doctor_inactive'])
        overlapping_schedules = Schedule.objects.filter(
            doctor=doctor,
            day_of_week=day_of_week,
            start__lt=end,
            end__gt=start
        ).exclude(id=self.instance.id)
        if overlapping_schedules.exists():
            raise ValidationError(ERROR_MESSAGES['schedule_overlap'])

        if start.minute % 15 != 0 or end.minute % 15 != 0:
            raise ValidationError(ERROR_MESSAGES['time_increments'])

        return cleaned_data

    def save(self, commit=True):
        schedule = super().save(commit=False)
        if commit:
            schedule.save()
        return schedule


class AdminScheduleForm(ScheduleForm):
    """
    Form for creating/editing schedules (admin).
    """
    class Meta:
        model = Schedule
        fields = ['doctor', 'start', 'end', 'day_of_week']
        widgets = {
            'day_of_week': forms.Select(choices=WEEKDAYS_CHOICES),
            'start': forms.TimeInput(format='%H:%M', attrs=START_END_ATTRS),
            'end': forms.TimeInput(format='%H:%M', attrs=START_END_ATTRS),
        }


class ScheduleViewForm(forms.ModelForm):
    """
    Form for viewing schedules.
    """
    class Meta:
        model = Schedule
        fields = ['doctor', 'start', 'end', 'day_of_week']
        widgets = {
            'day_of_week': forms.Select(choices=WEEKDAYS_CHOICES),
            'start': forms.TimeInput(format='%H:%M', attrs=START_END_ATTRS),
            'end': forms.TimeInput(format='%H:%M', attrs=START_END_ATTRS),
        }


class DoctorSearchForm(forms.Form):
    """
    Form for searching doctors.
    """
    fullname = forms.CharField(required=False, label='Имя доктора')
    specialization = forms.CharField(required=False, label='Специализация')
    username = forms.CharField(max_length=15, required=False, label='Имя пользователя')
    email = forms.EmailField(max_length=64, required=False, label='Email')
    phone = forms.CharField(max_length=15,
                            required=False,
                            help_text='Введите номер телефона без + и других символов',
                            label='Телефон')

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            return ''
        if phone and not phone.isdigit():
            raise ValidationError(ERROR_MESSAGES['phone_digits'])
        return phone.strip()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            return email.strip()
        return ''

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not is_safe_username(username) and username != '':
            raise ValidationError(ERROR_MESSAGES['username_invalid'])
        return username

    def clean_fullname(self):
        fullname = self.cleaned_data.get('fullname')
        if not fullname:
            return ''
        if any(char.isdigit() for char in fullname):
            raise ValidationError(ERROR_MESSAGES['fullname_numbers'])
        joined_fullname = ' '.join([word.strip() for word in fullname.split()])
        fullname_length = len(joined_fullname.split())
        if fullname_length != 2:
            raise ValidationError(ERROR_MESSAGES['fullname_two_words'])
        return joined_fullname

    def clean(self):
        cleaned_data = super().clean()
        for _, value in cleaned_data.items():
            if value != '':
                return cleaned_data
        raise ValidationError(ERROR_MESSAGES['search_param_required'])
