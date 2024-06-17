from django.test import TestCase, Client
from django.urls import reverse
from clinic.models import User, UserType, Visit, Schedule, Diagnosis, WeekDays
from django.http import HttpResponse
from datetime import date, time


class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser2', password='12345', user_level=UserType.PATIENT, fullname='Test User')

    def test_main_page_view(self):
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)

    def test_register_choose_view(self):
        response = self.client.get(reverse('register', kwargs={'role': 'patient'}))
        self.assertEqual(response.status_code, 200)

    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('login'), {'username': 'testuser2', 'password': '12345', 'fullname': 'Test User'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/{self.user.username}/')

    def test_logout_view(self):
        self.client.login(username='testuser2', password='12345')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/')

    def test_profile_view(self):
        self.client.login(username='testuser2', password='12345')
        response = self.client.get(reverse('profile', kwargs={'username': 'testuser2'}))
        self.assertEqual(response.status_code, 200)

    def test_profile_view_not_logged_in(self):
        response = self.client.get(reverse('profile', kwargs={'username': 'testuser2'}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=%2Ftestuser2%2F')
    
    def test_profile_view_other_user(self):
        other_user = User.objects.create_user(username='otheruser', password='12345', user_level=UserType.PATIENT, fullname='Other User')
        self.client.login(username='testuser2', password='12345')
        response = self.client.get(reverse('profile', kwargs={'username': 'otheruser'}))
        self.assertEqual(response.status_code, 403)

class RenderOtherProfileViewTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            username='testdoctor1',
            fullname='Test Doctor',
            email='testdoctor1@example.com',
            phone='1112223333',
            user_level=UserType.DOCTOR,
            password='testpassword'
        )
        self.patient = User.objects.create_user(
            username='testpatient1',
            fullname='Test Patient',
            email='testpatient1@example.com',
            phone='4445556666',
            user_level=UserType.PATIENT,
            password='testpassword'
        )
        self.client.login(username='testdoctor1', password='testpassword')
    def test_render_other_profile_doctor(self):
        response = self.client.get(reverse('profile', kwargs={'username': 'testpatient1'}))
        self.assertEqual(response.status_code, 200)
    def test_render_other_profile_patient(self):
        response = self.client.get(reverse('profile', kwargs={'username': 'testdoctor1'}))
        self.assertEqual(response.status_code, 200)
    def test_render_other_profile_unauthorized(self):
        response = self.client.get(reverse('profile', kwargs={'username': 'testuser1'}))
        self.assertEqual(response.status_code, 404)


class AuthViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser1',
            fullname='Test User',
            email='testuser1@example.com',
            phone='1234567890',
            user_level=UserType.PATIENT,
            password='testpassword'
        )

    def test_login_view_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_view_post(self):
        response = self.client.post(reverse('login'), {'username': 'testuser1', 'password': 'testpassword'})
        self.assertEqual(response.status_code, 302)  # Assuming a redirect on successful login

    def test_logout_view(self):
        self.client.login(username='testuser1', password='testpassword')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Assuming a redirect on logout

class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser2',
            fullname='Test User',
            email='testuser2@example.com',
            phone='1234567890',
            user_level=UserType.PATIENT,
            password='testpassword'
        )
        self.client.login(username='testuser2', password='testpassword')

    def test_profile_view_own(self):
        response = self.client.get(reverse('profile', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)

    def test_profile_view_other_forbidden(self):
        other_user = User.objects.create_user(
            username='otheruser',
            fullname='Other User',
            email='otheruser@example.com',
            phone='0987654321',
            user_level=UserType.PATIENT,
            password='otherpassword'
        )
        response = self.client.get(reverse('profile', kwargs={'username': other_user.username}))
        self.assertEqual(response.status_code, 403)


class RenderForDoctorViewTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            username='testdoctor2',
            fullname='Test Doctor',
            email='testdoctor@example.com',
            phone='1112223333',
            user_level=UserType.DOCTOR,
            password='testpassword'
        )
        self.patient = User.objects.create_user(
            username='testpatient2',
            fullname='Test Patient',
            email='testpatient@example.com',
            phone='4445556666',
            user_level=UserType.PATIENT,
            password='testpassword'
        )
        self.client.login(username='testdoctor2', password='testpassword')

    def test_render_patient_profile_for_doctor(self):
        response = self.client.get(reverse('profile', kwargs={'username': self.patient.username}))
        self.assertEqual(response.status_code, 200)

    def test_render_doctor_profile_for_doctor(self):
        response = self.client.get(reverse('profile', kwargs={'username': self.doctor.username}))
        self.assertEqual(response.status_code, 200)

    def test_render_for_doctor_invalid_user(self):
        response = self.client.get(reverse('profile', kwargs={'username': 'invaliduser'}))
        self.assertEqual(response.status_code, 404)


class SimpleViewTests(TestCase):
    def test_main_page_view(self):
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)

    def test_register_choose_view(self):
        response = self.client.get(reverse('register_choose'))
        self.assertEqual(response.status_code, 200)
    
    def test_login_view(self):
        response= self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_logout_view(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)

    def test_search_doctors_view(self):
        response = self.client.get(reverse('search_doctors'))
        self.assertEqual(response.status_code, 200)
    
    def test_edit_visit_view_unathorized(self):
        response = self.client.get(reverse('edit_visit', kwargs={'visit_id': 1}))
        self.assertEqual(response.status_code, 302)


class ToggleDiagnosisStatusViewTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            username='testdoctor3',
            fullname='Test Doctor',
            email='testdoctor@example.com',
            phone='1112223333',
            user_level=UserType.DOCTOR,
            password='testpassword'
        )
        self.patient = User.objects.create_user(
            username='testpatient3',
            fullname='Test Patient',
            email='testpatient@example.com',
            phone='4445556666',
            user_level=UserType.PATIENT,
            password='testpassword'
        )
        self.diagnosis = Diagnosis.objects.create(
            description='Initial diagnosis',
            patient=self.patient,
            doctor=self.doctor,
            is_active=True
        )
        self.client.login(username='testdoctor3', password='testpassword')


class UpdateScheduleViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testdoctor4',
            fullname='Test Doctor',
            email='testdoctor4@example.com',
            phone='1112223333',
            user_level=UserType.DOCTOR,
            password='testpassword'
        )
        self.client.login(username='testdoctor4', password='testpassword')
        self.schedule = Schedule.objects.create(
            doctor=self.user,
            start='09:00',
            end='17:00',
            day_of_week=WeekDays.MONDAY
        )

    def test_update_schedule_get(self):
        schedule_id = self.schedule.id  # Replace with the actual schedule ID
        response = self.client.get(reverse('update_schedule', kwargs={'schedule_id': schedule_id}))
        self.assertEqual(response.status_code, 200)

    def test_update_schedule_post(self):
        schedule_id = self.schedule.id  # Replace with the actual schedule ID
        response = self.client.post(reverse('update_schedule', kwargs={'schedule_id': schedule_id}), {
            'doctor': self.user.id,
            'start': '09:00',
            'end': '17:00',
            'day_of_week': WeekDays.MONDAY
        })
        self.assertEqual(response.status_code, 302)  # Assuming a redirect after successful update
        self.assertTrue(Schedule.objects.filter(doctor=self.user, day_of_week=WeekDays.MONDAY).exists())

class VisitViewSetTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(
            username='testdoctor5',
            fullname='Test Doctor',
            password='testpassword',
            user_level=UserType.DOCTOR,
            phone='1112223333',
            email="testdoctor5@example.com"
        )

        self.patient = User.objects.create_user(username='testpatient5', fullname='Test Patient', password='testpassword', user_level=UserType.PATIENT, phone='4445556666', email="testpatient5@example.com")
        self.client.login(username='testpatient5', password='testpassword')
        self.visit = Visit.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            date=date.today(),
            start=time(10, 0),
            end=time(11, 0),
            status='Active'
        )
    
    def test_visit_view_set_get(self):
        response = self.client.get(reverse('edit_visit', kwargs={'visit_id': self.visit.id}))
        self.assertEqual(response.status_code, 200)
    
    def test_visit_view_set_post(self):
        response = self.client.post(reverse('edit_visit', kwargs={'visit_id': self.visit.id}), {
            'doctor': self.doctor.id,
            'patient': self.patient.id,
            'date': date.today(),
            'start': time(11, 0),
            'end': time(12, 0),
            'status': 'Active'
        })
        self.assertEqual(response.status_code, 200)  # Assuming a redirect after successful update
        self.assertTrue(Visit.objects.filter(doctor=self.doctor, patient=self.patient, date=date.today(), start=time(10, 0), end=time(11, 0), status='Active').exists())
    
    def test_visit_view_set_update(self):
        response = self.client.put(reverse('edit_visit', kwargs={'visit_id': self.visit.id}), {
            'doctor': self.doctor.id,
            'patient': self.patient.id,
            'date': date.today(),
            'start': time(11, 0),
            'end': time(12, 0),
            'status': 'Active'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Visit.objects.filter(doctor=self.doctor, patient=self.patient, date=date.today(), start=time(10, 0), end=time(11, 0), status='Active').exists())


class ClinicModelTests(TestCase):
    def test_user_creation(self):
        user = User.objects.create_user(
            username='testuser6',
            fullname='Test User',
            email='testuser@example.com',
            phone='1234567890',
            user_level=UserType.PATIENT,
            password='testpassword'
        )
        self.assertEqual(user.username, 'testuser6')
        self.assertEqual(user.fullname, 'Test User')
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertEqual(user.phone, '1234567890')
        self.assertEqual(user.user_level, UserType.PATIENT)
    
    def test_visit_creation(self):
        doctor = User.objects.create_user(
            username='testdoctor6',
            fullname='Test Doctor',
            email='testdoctor@example.com',
            phone='1112223333',
            user_level=UserType.DOCTOR,
            password='testpassword'
        )
        patient = User.objects.create_user(
            username='testpatient6',
            fullname='Test Patient',
            email='testpatient@example.com',
            phone='4445556666',
            user_level=UserType.PATIENT,
            password='testpassword'
        )
        visit = Visit.objects.create(
            doctor=doctor,
            patient=patient,
            date=date.today(),
            start=time(10, 0),
            end=time(11, 0),
            status='Active'
        )
        self.assertEqual(visit.doctor, doctor)
        self.assertEqual(visit.patient, patient)
        self.assertEqual(visit.date, date.today())
        self.assertEqual(visit.start, time(10, 0))
        self.assertEqual(visit.end, time(11, 0))
        self.assertEqual(visit.status, 'Active')

