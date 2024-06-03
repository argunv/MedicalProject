from django import forms
from django.contrib.auth.forms import AuthenticationForm, BaseUserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from .models import User, Visit, Schedule, Diagnosis, UserType, AdminUserType, VisitStatus, WeekDays
from django.core.exceptions import PermissionDenied
# import datetime
from datetime import datetime, timedelta
from python_usernames import is_safe_username


def user_form_viewer(user_level: UserType):
    if user_level == UserType.PATIENT:
        return PatientUserForm
    elif user_level == UserType.DOCTOR:
        return DoctorUserForm
    elif user_level == UserType.ADMIN:
        return AdminUserForm
    elif user_level == UserType.SUPERUSER:
        return SuperUserForm
    else:
        raise PermissionDenied('You do not have permission to access this page.')

def register_user_form_viewer(user_level: UserType):
    if user_level == UserType.SUPERUSER:
        return SuperUserRegistrationForm
    elif user_level == UserType.ADMIN:
        return AdminUserRegistrationForm
    elif user_level == UserType.PATIENT:
        return PatientRegistrationForm
    elif user_level == UserType.DOCTOR:
        return DoctorRegistrationForm
    else:
        raise PermissionDenied('You do not have permission to access this page.')

class UserForm(forms.ModelForm):
    def clean_fullname(self):
        fullname = self.cleaned_data.get('fullname')
        if not fullname:
            raise ValidationError("Fullname can't be empty.")
        if any(char.isdigit() for char in fullname):
            raise ValidationError("Fullname can't contain numbers.")
        joined_fullname = ' '.join([word.strip() for word in fullname.split()])
        fullname_length = len(joined_fullname.split())
        if fullname_length != 2:
            raise ValidationError("Fullname must contain 2 words.")
        return joined_fullname

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > datetime.date.today():
            raise ValidationError("Date of birth cannot be in the future.")
        return dob

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            return 
        if phone and not phone.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        return phone.strip()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email cannot be empty.")
        return email.strip()
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not is_safe_username(username):
            raise ValidationError("Username invalid. Try another username.")
        return username

    def clean_user_level(self):
        user_level = self.cleaned_data.get('user_level')
        specialty = self.data.get('specialty')
        if user_level not in UserType:
            raise ValidationError("This type of user doesn't exists")
        if user_level != UserType.DOCTOR and specialty:
            raise ValidationError("Specialty is not allowed for this type of user.")
        return user_level

    def clean_specialty(self):
        specialty = self.cleaned_data.get('specialty')
        user_level = self.data.get('user_level')

        if user_level != UserType.DOCTOR and specialty:
            raise ValidationError("Specialty is not allowed for this user_level.")

        if user_level == UserType.DOCTOR:
            if not specialty:
                raise ValidationError("Specialty is required for doctors.")
            if not specialty.isalpha():
                raise ValidationError("Specialty must contain only letters.")

class PatientUserForm(UserForm):
    class Meta:
        model = User
        fields = ['username', 'fullname', 'email', 'phone']

class DoctorUserForm(UserForm):
    class Meta:
        model = User
        fields = ['username', 'fullname', 'email', 'phone', 'specialty']

class AdminUserForm(UserForm):
    class Meta:
        model = User
        fields = ['username', 'fullname', 'email', 'phone', 'specialty', 'is_active']

class SuperUserForm(UserForm):
    class Meta:
        model = User
        fields = ['username', 'fullname', 'email', 'phone', 'specialty', 'user_level', 'is_active']

class UserRegistrationForm(BaseUserCreationForm, UserForm):
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise ValidationError("Phone number is required.")
        if not phone.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        if User.objects.filter(phone=phone).exists():
            raise ValidationError("This phone number is already registered.")
        return phone

class SuperUserRegistrationForm(UserRegistrationForm):
    class Meta:
        model = User
        fields = ['username', 'fullname', 'email', 'phone', 'user_level', 'is_active', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        # Save the password if set
        if 'new_password1' in self.cleaned_data and self.cleaned_data['new_password1']:
            user.set_password(self.cleaned_data['new_password1'])
        if commit:
            user.save()
        return user

class AdminUserRegistrationForm(UserRegistrationForm):
    class Meta:
        model = User
        fields = ['username', 'fullname', 'email', 'phone', 'is_active', 'password1', 'password2']

    user_level = forms.TypedChoiceField(coerce=int, choices=AdminUserType.choices, initial=AdminUserType.PATIENT)

    def save(self, commit=True):
        user = super().save(commit=False)
        # Save the password if set
        if 'new_password1' in self.cleaned_data and self.cleaned_data['new_password1']:
            user.set_password(self.cleaned_data['new_password1'])
        if commit:
            user.save()
        return user

class PatientRegistrationForm(UserRegistrationForm):
    class Meta:
        model = User
        fields = ['username', 'fullname', 'email', 'phone', 'user_level']

class DoctorRegistrationForm(UserRegistrationForm):
    class Meta:
        model = User
        fields = ['username', 'fullname', 'email', 'phone', 'user_level', 'specialty']
        required_fields = ['username', 'fullname', 'email', 'phone', 'user_level', 'specialty']

class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start': forms.NumberInput(attrs={'min': 0, 'max': 96}),
            'end': forms.NumberInput(attrs={'min': 0, 'max': 96}),
        }

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        patient = cleaned_data.get('patient')
        start = cleaned_data.get('start')
        end = cleaned_data.get('end')
        date = cleaned_data.get('date')
        status = cleaned_data.get('status')

        if not doctor or not patient:
            raise ValidationError("Both doctor and patient must have a user account.")
        if doctor == patient:
            raise ValidationError("Doctor cannot have a visit with themselves.")
        if doctor.user_level != UserType.DOCTOR:
            raise ValidationError("The assigned doctor must have the Doctor user level.")
        if patient.user_level != UserType.PATIENT:
            raise ValidationError("The assigned patient must have the Patient user level.")
        if not doctor.is_active:
            raise ValidationError("The doctor is not active.")
        if start >= end:
            raise ValidationError("Start time must be before end time.")
        if start < 0 or end > 96:
            raise ValidationError("Start and end times must be within the range of 0 to 96.")
        
        # Проверка на занятость доктора
        overlapping_visits = Visit.objects.filter(
            doctor=doctor,
            date=date,
            start__lt=end,
            end__gt=start
        ).exclude(id=self.instance.id)

        if overlapping_visits.exists():
            other_patient_visits = overlapping_visits.exclude(patient=patient)
            if other_patient_visits.exists():
                raise ValidationError("The doctor already has a visit scheduled during this time.")

        # Проверка на соответствие расписанию доктора
        day_of_week = date.weekday()
        schedule = Schedule.objects.filter(
            doctor=doctor,
            day_of_week=day_of_week,
            start__lte=start,
            end__gte=end
        )
        if not schedule.exists():
            raise ValidationError("The visit is outside the doctor's schedule.")

        current_datetime = datetime.now()
        visit_datetime = datetime.combine(date, datetime.min.time()) + timedelta(minutes=start * 15)  # Assuming each unit of start is 15 minutes

        if visit_datetime > current_datetime and status in [VisitStatus.MISSED, VisitStatus.VISITED]:
            raise ValidationError("A future visit cannot have the status 'Visited' or 'Missed'.")
        if visit_datetime <= current_datetime and status == VisitStatus.SCHEDULED:
            raise ValidationError("A past visit cannot have the status 'Scheduled'.")

        return cleaned_data

class VisitCreationForm(VisitForm):
    class Meta:
        model = Visit
        fields = ['doctor', 'patient', 'date', 'start', 'end', 'description']
        required_fields = ['doctor', 'patient', 'date', 'start', 'end']

class VisitViewForm(VisitForm):
    class Meta:
        model = Visit
        fields = ['doctor', 'patient', 'date', 'start', 'end', 'status', 'description']
        required_fields = ['doctor', 'patient', 'date', 'start', 'end', 'status']

class DiagnosisForm(forms.ModelForm):
    class Meta:
        model = Diagnosis
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        patient = cleaned_data.get('patient')
        description = cleaned_data.get('description')
        if not doctor or not patient:
            raise ValidationError('Doctor and patient are required.')
        if doctor.user_level != UserType.DOCTOR:
            raise ValidationError("The assigned doctor must have the Doctor user level.")
        if patient.user_level != UserType.PATIENT:
            raise ValidationError("The assigned patient must have the Patient user level.")
        if not doctor.is_active:
            raise ValidationError("The doctor is not active.")
        if not description:
            raise ValidationError('Description is required.')
        if len(description) < 10:
            raise ValidationError('Description must be more detailed.')

        return cleaned_data

class ScheduleForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        doctor = self.cleaned_data.get('doctor')
        print(f'Doctor 2: {doctor}')
        start = cleaned_data.get('start')
        end = cleaned_data.get('end')
        day_of_week = cleaned_data.get('day_of_week')

        if not doctor:
            raise ValidationError("Doctor must be assigned.")
        if not doctor.is_active:
            raise ValidationError("The doctor is not active.")
        if not isinstance(start, int) or not isinstance(end, int):
            raise ValidationError("Start and end must be integers.")
        overlapping_schedules = Schedule.objects.filter(
            doctor=doctor,
            day_of_week=day_of_week,
            start__lt=end,
            end__gt=start
        ).exclude(id=self.instance.id)
        if overlapping_schedules.exists():
            raise ValidationError("This schedule overlaps with an existing schedule for the doctor.")

        return cleaned_data

    def save(self, commit=True):
        schedule = super().save(commit=False)
        if self.doctor:
            schedule.doctor = self.doctor
        if commit:
            schedule.save()
        return schedule

class AdminScheduleForm(ScheduleForm):
    class Meta:
        model = Schedule
        fields = ['doctor', 'start', 'end', 'day_of_week']
        widgets = {
            'day_of_week': forms.Select(choices=WeekDays),
            'start': forms.NumberInput(attrs={'min': 0, 'max': 96}),
            'end': forms.NumberInput(attrs={'min': 0, 'max': 96}),
        }

class ScheduleViewForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['start', 'end', 'day_of_week']
        widgets = {
            'day_of_week': forms.Select(choices=WeekDays),
            'start': forms.NumberInput(attrs={'min': 0, 'max': 96}),
            'end': forms.NumberInput(attrs={'min': 0, 'max': 96}),
        }

    def save(self, commit=True):
        schedule = super().save(commit=False)
        if self.instance.pk is None:  # For new instances
            schedule.doctor = self.doctor
        if commit:
            schedule.save()
        return schedule