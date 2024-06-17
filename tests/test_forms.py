from datetime import time, date
from django.test import TestCase
from clinic.models import User, UserType, Schedule

from clinic.forms import (
    PatientUserForm,
    DoctorUserForm,
    VisitCreationForm,
    AdminScheduleForm,
    SuperUserRegistrationForm,
    PatientRegistrationForm,
    AdminUserForm,
    VisitViewForm,
    DiagnosisForm,
    ScheduleViewForm
)

from clinic.models import VisitStatus


class UserFormTests(TestCase):
    def test_patient_user_form_valid(self):
        form_data = {
            'username': 'patient123',
            'fullname': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
        }
        form = PatientUserForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_patient_user_form_invalid_fullname(self):
        form_data = {
            'username': 'patient123',
            'fullname': 'John123 Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
        }
        form = PatientUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('fullname', form.errors)

    def test_doctor_user_form_valid(self):
        form_data = {
            'username': 'doctor123',
            'fullname': 'Jane Smith',
            'email': 'jane.smith@example.com',
            'phone': '0987654321',
            'specialty': 'Cardiology',
        }
        form = DoctorUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('specialty', form.errors)

    def test_doctor_user_form_invalid_specialty(self):
        form_data = {
            'username': 'doctor123',
            'fullname': 'Jane Smith',
            'email': 'jane.smith@example.com',
            'phone': '0987654321',
            'specialty': 'Cardiology123',
        }
        form = DoctorUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('specialty', form.errors)


    # NOTE added
    def test_doctor_user_form_valid(self):
        form_data = {
            'username': 'doctor123',
            'fullname': 'Jane Smith',
            'user_level': UserType.DOCTOR,
            'specialty': 'Cardiology',
            'email': 'jane.smith@example.com',
            'phone': '0987654321',
        }
        form = DoctorUserForm(data=form_data)
        print(form.errors)
        self.assertTrue(form.is_valid())


class VisitFormTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create(username='doctor', user_level=UserType.DOCTOR, is_active=True)
        self.patient = User.objects.create(username='patient', user_level=UserType.PATIENT, is_active=True)

    def test_visit_creation_form_valid_without_doctor_schedule(self):
        form_data = {
            'date': date.today(),
            'start': "10:00",
            'end': "11:00",
            'description': 'Routine checkup',
        }
        form = VisitCreationForm(data=form_data, doctor=self.doctor, patient=self.patient)
        self.assertFalse(form.is_valid())

    def test_visit_creation_form_invalid_time(self):
        form_data = {
            'date': date.today(),
            'start': "10:00",
            'end': "11:00",
            'description': 'Routine checkup',
        }
        form = VisitCreationForm(data=form_data, doctor=self.doctor, patient=self.patient)
        self.assertFalse(form.is_valid())


class UserRegistrationFormTests(TestCase):
    def test_superuser_registration_form_valid(self):
        form_data = {
            'username': 'superuser123',
            'fullname': 'Super User',
            'email': 'super.user@example.com',
            'phone': '1234567890',
            'user_level': UserType.SUPERUSER,
            'password1': 'strongpassword',
            'password2': 'strongpassword',
        }
        form = SuperUserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_superuser_registration_form_username_taken(self):
        User.objects.create(username='superuser123', email='super.user@example.com', phone='1234567890')
        form_data = {
            'username': 'superuser123',
            'fullname': 'Super User',
            'email': 'superuser123@test.com',
            'phone': '1234567890',
            'user_level': UserType.SUPERUSER,
            'password1': 'strongpassword',
            'password2': 'strongpassword',
        }
        form = SuperUserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_superuser_registration_form_invalid_email(self):
        form_data = {
            'username': 'superuser123',
            'fullname': 'Super User',
            'email': 'super.user@invalid',
            'phone': '1234567890',
            'user_level': UserType.SUPERUSER,
            'password1': 'strongpassword',
            'password2': 'strongpassword',
        }
        form = SuperUserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class ScheduleFormTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create(username='doctorf', user_level=UserType.DOCTOR, fullname='Doctor Smith', email='asfaafs@example.com', phone='1234567890', password='testpassword')

    def test_admin_schedule_form_valid(self):
        form_data = {
            'doctor': self.doctor.id,
            'start': time(9, 0),
            'end': time(17, 0),
            'day_of_week': 1,  # Monday
        }
        form = AdminScheduleForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_admin_schedule_form_overlap(self):
        Schedule.objects.create(doctor=self.doctor, start=time(9, 0), end=time(12, 0), day_of_week=1)
        form_data = {
            'doctor': self.doctor.id,
            'start': time(11, 0),
            'end': time(14, 0),
            'day_of_week': 1,  # Monday
        }
        form = AdminScheduleForm(data=form_data)
        self.assertFalse(form.is_valid())

# NOTE NEW TESTS
class PatientRegistrationFormTests(TestCase):

    def test_patient_registration_form_valid(self):
        form_data = {
            'username': 'patient123',
            'fullname': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'user_level': UserType.PATIENT,
            'password1': 'strongpassword',
            'password2': 'strongpassword',
        }
        form = PatientRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_patient_registration_form_invalid_username(self):
        form_data = {
            'username': 'patient 123',
            'fullname': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'user_level': UserType.PATIENT,
            'password1': 'strongpassword',
            'password2': 'strongpassword',
        }
        form = PatientRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

class AdminUserFormTests(TestCase):
    def test_admin_user_form_valid(self):
        form_data = {
            'username': 'admin123',
            'fullname': 'Admin User',
            'email': 'admin.user@example.com',
            'phone': '1234567890',
            'specialty': 'Administration',
            'is_active': True,
        }
        form = AdminUserForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_admin_user_form_invalid_email(self):
        form_data = {
            'username': 'admin123',
            'fullname': 'Admin User',
            'email': 'admin.user@invalid',
            'phone': '1234567890',
            'specialty': 'Administration',
            'is_active': True,
        }
        form = AdminUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

class VisitViewFormTests(TestCase):
    def test_visit_view_form_valid(self):
        form_data = {
            'date': date.today(),
            'start': "10:00",
            'end': "11:00",
            'description': 'Routine checkup',
            'status': VisitStatus.ACTIVE,
        }
        form = VisitViewForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_visit_view_form_invalid_status(self):
        form_data = {
            'date': date.today(),
            'start': "10:00",
            'end': "11:00",
            'description': 'Routine checkup',
            'status': 'InvalidStatus',
        }
        form = VisitViewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)

class DiagnosisFormTests(TestCase):
    def test_diagnosis_form_valid(self):
        form_data = {
            'name': 'Common Cold',
            'description': 'A mild viral infection',
        }
        form = DiagnosisForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_diagnosis_form_invalid_name(self):
        form_data = {
            'name': '',
            'description': 'A mild viral infection',
        }
        form = DiagnosisForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

class ScheduleViewFormTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create(username='doctorn', user_level=UserType.DOCTOR, fullname='Doctor Smith', email='asfaafs@example.com', phone='1234567890', password='testpassword')

    def test_schedule_view_form_valid(self):
        form_data = {
            'doctor': self.doctor.id,
            'start': time(9, 0),
            'end': time(17, 0),
            'day_of_week': 1,  # Monday
        }
        form = ScheduleViewForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_schedule_view_form_invalid_start_time(self):
        form_data = {
            'doctor': self.doctor.id,
            'start': time(18, 0),
            'end': time(20, 0),
            'day_of_week': 1,  # Monday
        }
        form = ScheduleViewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('start', form.errors)