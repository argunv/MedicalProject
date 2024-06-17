from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.urls import reverse
from clinic.admin import UserAdmin, VisitAdmin, ScheduleAdmin, DiagnosisAdmin
from clinic.models import User, Visit, Schedule, Diagnosis, UserType
from random import randint


USER_KWARGS = {'email': f'test{randint(0, 100)}@example.com', 'phone': '1234567890', 'fullname': 'Test User'}

class UserAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = UserAdmin(User, self.site)

    def test_list_display(self):
        self.assertEqual(
            self.admin.list_display,
            ('username', 'fullname', 'email', 'phone', 'user_level', 'created_at')
        )

    def test_search_fields(self):
        self.assertEqual(
            self.admin.search_fields,
            ('username', 'fullname', 'email', 'phone')
        )

    def test_list_filter(self):
        self.assertEqual(
            self.admin.list_filter,
            ('user_level', 'created_at')
        )

    def test_ordering(self):
        self.assertEqual(
            self.admin.ordering,
            ('created_at',)
        )


class AdminTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.user_admin = UserAdmin(User, self.site)
        self.visit_admin = VisitAdmin(Visit, self.site)
        self.schedule_admin = ScheduleAdmin(Schedule, self.site)
        self.diagnosis_admin = DiagnosisAdmin(Diagnosis, self.site)

    def test_user_admin_list_display(self):
        self.assertEqual(self.user_admin.list_display, ('username', 'fullname', 'email', 'phone', 'user_level', 'created_at'))

    def test_user_admin_search_fields(self):
        self.assertEqual(self.user_admin.search_fields, ('username', 'fullname', 'email', 'phone'))

    def test_user_admin_list_filter(self):
        self.assertEqual(self.user_admin.list_filter, ('user_level', 'created_at'))

    def test_user_admin_ordering(self):
        self.assertEqual(self.user_admin.ordering, ('created_at',))

    def test_visit_admin_list_display(self):
        self.assertEqual(self.visit_admin.list_display, ('patient', 'doctor', 'start', 'end', 'status'))

    def test_visit_admin_search_fields(self):
        self.assertEqual(self.visit_admin.search_fields, ('patient__fullname', 'doctor__fullname', 'status'))

    def test_visit_admin_list_filter(self):
        self.assertEqual(self.visit_admin.list_filter, ('status', 'start', 'end'))

    def test_visit_admin_ordering(self):
        self.assertEqual(self.visit_admin.ordering, ('start',))

    def test_schedule_admin_list_display(self):
        self.assertEqual(self.schedule_admin.list_display, ('doctor', 'day_of_week', 'start', 'end'))

    def test_schedule_admin_search_fields(self):
        self.assertEqual(self.schedule_admin.search_fields, ('doctor__fullname', 'day_of_week'))

    def test_schedule_admin_list_filter(self):
        self.assertEqual(self.schedule_admin.list_filter, ('day_of_week', 'doctor'))

    def test_schedule_admin_ordering(self):
        self.assertEqual(self.schedule_admin.ordering, ('doctor', 'day_of_week'))

    def test_diagnosis_admin_list_display(self):
        self.assertEqual(self.diagnosis_admin.list_display, ('patient', 'doctor', 'description', 'is_active'))

    def test_diagnosis_admin_search_fields(self):
        self.assertEqual(self.diagnosis_admin.search_fields, ('patient__fullname', 'doctor__fullname', 'description'))

    def test_diagnosis_admin_list_filter(self):
        self.assertEqual(self.diagnosis_admin.list_filter, ('is_active',))

    def test_diagnosis_admin_ordering(self):
        self.assertEqual(self.diagnosis_admin.ordering, ('patient', 'doctor'))

    def test_user_admin_delete_model(self):
        user = User(username='testuseru', fullname='Test User', email='test@example.com', phone='1234567890', user_level=UserType.DOCTOR)
        user.save()
        self.user_admin.delete_model(request=None, obj=user)
        self.assertEqual(User.objects.count(), 0)

    def test_user_admin_delete_queryset(self):
        user1 = User(username='testusero1', fullname='Test User 1', email='test1@example.com', phone='1234567890', user_level=UserType.DOCTOR)
        user2 = User(username='testusero2', fullname='Test User 2', email='test2@example.com', phone='1234567890', user_level=UserType.DOCTOR)
        user1.save()
        user2.save()
        queryset = User.objects.filter(username__startswith='testusero')
        self.user_admin.delete_queryset(request=None, queryset=queryset)
        self.assertEqual(User.objects.count(), 0)

    def test_visit_admin_get_form(self):
        form = self.visit_admin.get_form(request=None, obj=None)
        self.assertIsNotNone(form)

    def test_schedule_admin_get_form(self):
        form = self.schedule_admin.get_form(request=None, obj=None)
        self.assertIsNotNone(form)

    def test_diagnosis_admin_get_form(self):
        form = self.diagnosis_admin.get_form(request=None, obj=None)
        self.assertIsNotNone(form)
