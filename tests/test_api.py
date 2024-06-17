from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from rest_framework.authtoken.models import Token
from clinic.models import User, Visit, Diagnosis, Schedule
from clinic.serializers import DiagnosisSerializer, ScheduleSerializer, VisitSerializer

class DiagnosisViewSetTests(APITestCase):

    def setUp(self):
        self.doctor = User.objects.create_user(
            username='doctor1',
            fullname='Doctor User',
            email='doctor@example.com',
            phone='1234567890',
            user_level=1,
            password='doctorpassword123'
        )
        self.patient = User.objects.create_user(
            username='patient1',
            fullname='Patient User',
            email='patient@example.com',
            phone='0987654321',
            user_level=0,
            password='patientpassword123'
        )
        self.diagnosis = Diagnosis.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            description='Test Diagnosis'
        )
        self.token = Token.objects.create(user=self.doctor)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def tearDown(self):
        self.diagnosis.delete()
        self.patient.delete()
        self.doctor.delete()

    def test_list_diagnoses(self):
        url = reverse('diagnosis-list')
        response = self.client.get(url)
        diagnoses = Diagnosis.objects.all()
        serializer = DiagnosisSerializer(diagnoses, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_diagnosis(self):
        url = reverse('diagnosis-detail', kwargs={'pk': self.diagnosis.pk})
        response = self.client.get(url)
        serializer = DiagnosisSerializer(self.diagnosis)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_update_diagnosis(self):
        url = reverse('diagnosis-detail', kwargs={'pk': self.diagnosis.pk})
        updated_diagnosis_data = {
            'doctor': str(self.doctor.id),
            'patient': str(self.patient.id),
            'description': 'Updated Diagnosis'
        }
        response = self.client.put(url, updated_diagnosis_data, format='json')
        self.diagnosis.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.diagnosis.description, 'Updated Diagnosis')

    def test_delete_diagnosis(self):
        url = reverse('diagnosis-detail', kwargs={'pk': self.diagnosis.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Diagnosis.objects.count(), 0)


class ScheduleViewSetTests(APITestCase):

    def setUp(self):
        self.doctor = User.objects.create_user(
            username='doctor2',
            fullname='Doctor User',
            email='doctor@example.com',
            phone='1234567890',
            user_level=1,
            password='doctorpassword123'
        )
        self.token = Token.objects.create(user=self.doctor)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.schedule = Schedule.objects.create(
            doctor=self.doctor,
            day_of_week=1,
            start='09:00',  # Format HH:MM
            end='10:00'
        )

    def tearDown(self):
        self.schedule.delete()
        self.doctor.delete()

    def test_list_schedules(self):
        url = reverse('schedule-list')
        response = self.client.get(url)
        schedules = Schedule.objects.all()
        serializer = ScheduleSerializer(schedules, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_schedule(self):
        url = reverse('schedule-list')
        new_schedule_data = {
            'doctor': str(self.doctor.id),
            'day_of_week': 2,
            'start': '10:00',  # Format HH:MM
            'end': '11:00'
        }
        response = self.client.post(url, new_schedule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Schedule.objects.count(), 2)

    def test_retrieve_schedule(self):
        url = reverse('schedule-detail', kwargs={'pk': self.schedule.pk})
        response = self.client.get(url)
        serializer = ScheduleSerializer(self.schedule)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_update_schedule(self):
        url = reverse('schedule-detail', kwargs={'pk': self.schedule.pk})
        updated_schedule_data = {
            'doctor': str(self.doctor.id),
            'day_of_week': 3,
            'start': '11:00',  # Format HH:MM
            'end': '12:00'
        }
        response = self.client.put(url, updated_schedule_data, format='json')
        self.schedule.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.schedule.day_of_week, 3)
        self.assertEqual(self.schedule.start.strftime('%H:%M'), '11:00')  # Check format HH:MM
        self.assertEqual(self.schedule.end.strftime('%H:%M'), '12:00')

    def test_delete_schedule(self):
        url = reverse('schedule-detail', kwargs={'pk': self.schedule.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Schedule.objects.count(), 0)


class VisitViewSetTests(APITestCase):

    def setUp(self):
        self.doctor = User.objects.create_user(
            username='doctor3',
            fullname='Doctor User',
            email='doctor@example.com',
            phone='1234567890',
            user_level=1,
            password='doctorpassword123'
        )
        self.patient = User.objects.create_user(
            username='patient2',
            fullname='Patient User',
            email='patient@example.com',
            phone='0987654321',
            user_level=0,
            password='patientpassword123'
        )
        self.visit = Visit.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            date='2023-06-17',
            start='09:00',  # Format HH:MM
            end='10:00',
            status='active',
            description='Routine checkup'
        )
        self.token = Token.objects.create(user=self.doctor)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def tearDown(self):
        self.visit.delete()
        self.patient.delete()
        self.doctor.delete()

    def test_list_visits(self):
        url = reverse('visit-list')
        response = self.client.get(url)
        visits = Visit.objects.all()
        serializer = VisitSerializer(visits, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_visit(self):
        url = reverse('visit-list')
        new_visit_data = {
            'doctor': str(self.doctor.id),
            'patient': str(self.patient.id),
            'date': '2023-06-18',
            'start': '10:00',  # Format HH:MM
            'end': '11:00',
            'status': 'active',
            'description': 'Follow-up appointment'
        }
        response = self.client.post(url, new_visit_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Visit.objects.count(), 2)

    def test_retrieve_visit(self):
        url = reverse('visit-detail', kwargs={'pk': self.visit.pk})
        response = self.client.get(url)
        serializer = VisitSerializer(self.visit)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_update_visit(self):
        url = reverse('visit-detail', kwargs={'pk': self.visit.pk})
        updated_visit_data = {
            'doctor': str(self.doctor.id),
            'patient': str(self.patient.id),
            'date': '2023-06-19',
            'start': '11:00',  # Format HH:MM
            'end': '12:00',
            'status': 'visited',
            'description': 'Updated visit description'
        }
        response = self.client.put(url, updated_visit_data, format='json')
        self.visit.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.visit.date.strftime('%Y-%m-%d'), '2023-06-19')  # Check format YYYY-MM-DD
        self.assertEqual(self.visit.start.strftime('%H:%M'), '11:00')  # Check format HH:MM
        self.assertEqual(self.visit.end.strftime('%H:%M'), '12:00')  # Check format HH:MM
        self.assertEqual(self.visit.status, 'visited')
        self.assertEqual(self.visit.description, 'Updated visit description')

    def test_delete_visit(self):
        url = reverse('visit-detail', kwargs={'pk': self.visit.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Visit.objects.count(), 0)
