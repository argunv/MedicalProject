from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from .views import (
    main_page_view, register_choose_view,
    register, login_view, logout_view,
    profile_view,
    search_doctors_view,
    edit_visit,
    doctor_schedule, edit_schedule,
    update_schedule, toggle_diagnosis_status,

    VisitViewSet, UserViewSet, DiagnosisViewSet, ScheduleViewSet
)


# Define constants for URL patterns
API_PREFIX = "api/"
REGISTER_URL = "register/<role>/"
LOGIN_URL = "login/"
LOGOUT_URL = "logout/"
TOGGLE_DIAGNOSIS_STATUS_URL = "toggle_diagnosis_status/<uuid:diagnosis_id>/"
UPDATE_SCHEDULE_URL = "schedule/<int:schedule_id>/update/"
MAIN_PAGE_URL = ""
REGISTER_CHOOSE_URL = "register_choose/"
EDIT_VISIT_URL = "visit/edit/<int:visit_id>/"
DOCTOR_SCHEDULE_URL = "doctor/<int:doctor_id>/schedule/"
EDIT_SCHEDULE_URL = "doctor/schedule/edit/"
SEARCH_DOCTORS_URL = "search/"
PROFILE_URL = "<str:username>/"
API_TOKEN_URL = "api-token-auth/"

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"visits", VisitViewSet)
router.register(r"diagnoses", DiagnosisViewSet)
router.register(r"schedules", ScheduleViewSet)
api_patterns = [
    path("", include(router.urls)),
]

urlpatterns = [
    path(API_PREFIX, include(api_patterns)),
    path(REGISTER_URL, register, name="register"),
    path(LOGIN_URL, login_view, name="login"),
    path(LOGOUT_URL, logout_view, name="logout"),
    path(API_TOKEN_URL, obtain_auth_token, name="obtain_auth_token"),
    path(TOGGLE_DIAGNOSIS_STATUS_URL, toggle_diagnosis_status, name="toggle_diagnosis_status"),
    path(UPDATE_SCHEDULE_URL, update_schedule, name="update_schedule"),
    path(MAIN_PAGE_URL, main_page_view, name="main"),
    path(REGISTER_CHOOSE_URL, register_choose_view, name="register_choose"),
    path(EDIT_VISIT_URL, edit_visit, name="edit_visit"),
    path(DOCTOR_SCHEDULE_URL, doctor_schedule, name="doctor_schedule"),
    path(EDIT_SCHEDULE_URL, edit_schedule, name="edit_schedule"),
    path(SEARCH_DOCTORS_URL, search_doctors_view, name="search_doctors"),
    path(PROFILE_URL, profile_view, name="profile"),
]
