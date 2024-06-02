from django.urls import path, include
from django.shortcuts import render
from .views import (
    main_page_view, 
    register, login_view, logout_view, 
    profile_view, 
    create_visit, edit_visit,
    doctor_schedule, edit_schedule,
    UserViewSet, VisitViewSet, DiagnosisViewSet, 
    update_schedule, toggle_diagnosis_status
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"visits", VisitViewSet)
router.register(r"diagnoses", DiagnosisViewSet)

api_patterns = [
    path("", include(router.urls)),
]

urlpatterns = [
    path("api/", include(api_patterns)),
    path("register/<role>/", register, name="register"),
    path("login/", login_view, name="login"),
    path('logout/', logout_view, name='logout'),
    path("<str:username>/", profile_view, name="profile"),
    path("schedule/<schedule_id>/update/", update_schedule, name="update_schedule"),
    path("diagnosis/<diagnosis_id>/toggle_status/", toggle_diagnosis_status, name="toggle_diagnosis_status"),
    path("", main_page_view, name="main"),
    path('visit/create/', create_visit, name='create_visit'),
    path('visit/edit/<int:visit_id>/', edit_visit, name='edit_visit'),
    path('doctor/<int:doctor_id>/schedule/', doctor_schedule, name='doctor_schedule'),
    path('doctor/schedule/edit/', edit_schedule, name='edit_schedule'),
]