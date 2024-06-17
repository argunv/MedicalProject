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
    ScheduleViewForm,
    DoctorSearchForm,
    SuperUserForm,
    AdminUserRegistrationForm,
    DoctorRegistrationForm,
    user_form_viewer,
    register_user_form_viewer
)

from clinic.models import VisitStatus
from django.core.exceptions import PermissionDenied, ValidationError
from datetime import datetime, timedelta
from django.test import TestCase
from clinic.models import User, UserType
from clinic.forms import VisitForm, ERROR_MESSAGES
from django.test import TestCase
from clinic.forms import UserForm, ERROR_MESSAGES
from datetime import datetime, timedelta


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

class AdminUserFormTests(TestCase):
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
    def test_user_form_viewer_admin(self):
        form_class = user_form_viewer(UserType.ADMIN)
        self.assertEqual(form_class, AdminUserForm)

    def test_user_form_viewer_invalid_user_level(self):
        with self.assertRaises(PermissionDenied):
            user_form_viewer('InvalidUserLevel')

    def test_register_user_form_viewer_superuser(self):
        form_class = register_user_form_viewer(UserType.SUPERUSER)
        self.assertEqual(form_class, SuperUserRegistrationForm)

    def test_register_user_form_viewer_admin(self):
        form_class = register_user_form_viewer(UserType.ADMIN)
        self.assertEqual(form_class, AdminUserRegistrationForm)

    def test_register_user_form_viewer_patient(self):
        form_class = register_user_form_viewer(UserType.PATIENT)
        self.assertEqual(form_class, PatientRegistrationForm)

    def test_register_user_form_viewer_doctor(self):
        form_class = register_user_form_viewer(UserType.DOCTOR)
        self.assertEqual(form_class, DoctorRegistrationForm)

    def test_register_user_form_viewer_invalid_user_level(self):
        with self.assertRaises(PermissionDenied):
            register_user_form_viewer('InvalidUserLevel')
            user_form_viewer('InvalidUserLevel')


class DiagnosisFormTests(TestCase):
    def test_diagnosis_form_clean_valid(self):
        form_data = {
            'doctor': User.objects.create(username='doctor1', user_level=UserType.DOCTOR, fullname='Doctor Smith', email='doctor@example.com', phone='1234567890', password='testpassword'),
            'patient': User.objects.create(username='patient1', user_level=UserType.PATIENT, fullname='John Doe', email='patient@example.com', phone='1234567890', password='testpassword'),
            'description': 'Detailed description of the diagnosis',
        }
        form = DiagnosisForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_diagnosis_form_clean_invalid_doctor_patient(self):
        form_data = {
            'doctor': None,
            'patient': User.objects.create(username='patient1', user_level=UserType.PATIENT, fullname='John Doe', email='patient@example.com', phone='1234567890', password='testpassword'),
            'description': 'Detailed description of the diagnosis',
        }
        form = DiagnosisForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('doctor', form.errors)


class SuperUserFormTests(TestCase):
    def test_superuser_form_invalid_user_level(self):
        form_data = {
            'username': 'adminusertest2',
            'fullname': 'Admin User',
            'email': 'admin@example.com',
            'phone': '1234567890',
            'specialty': 'Admin Specialty',
            'user_level': UserType.PATIENT,
            'is_active': True,
            'is_superuser': True,
            'is_staff': True,
        }
        form = SuperUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('user_level', form.errors)


class VisitCreationFormTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create(username='doctor1', user_level=UserType.DOCTOR, fullname='Doctor Smith', email='doctor@example.com', phone='1234567890', password='testpassword')
        self.patient = User.objects.create(username='patient1', user_level=UserType.PATIENT, fullname='John Doe', email='patient@example.com', phone='1234567890', password='testpassword')

    def test_visit_creation_form_clean_invalid_missing_date(self):
        form_data = {
            'start': time(9, 0),
            'end': time(10, 0),
            'description': 'Test visit',
        }
        form = VisitCreationForm(data=form_data, doctor=self.doctor, patient=self.patient)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)
