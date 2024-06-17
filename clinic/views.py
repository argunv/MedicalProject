from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
import calendar
from .models import User, Visit, Schedule, Diagnosis, UserType, VisitStatus
from rest_framework import viewsets
from .serializers import UserSerializer, VisitSerializer, ScheduleSerializer, DiagnosisSerializer
from datetime import date
from rest_framework.permissions import IsAuthenticated, AllowAny


from .forms import (
    register_user_form_viewer,
    ScheduleViewForm, VisitViewForm, VisitCreationForm,
    DoctorSearchForm
)


ROLES = {'patient': 0, 'doctor': 1, 'admin': 2, 'superuser': 3}


def main_page_view(request):
    """
    Render the main page view.

    Args:
        request: The HTTP request object.

    Returns:
        The rendered main page view.
    """
    return render(request, 'base_generic.html')


def register_choose_view(request):
    """
    Render the register choose view.

    Args:
        request: The HTTP request object.

    Returns:
        The rendered register choose view.
    """
    return render(request, 'register/index.html')


def register(request, role: str):
    """
    Register a user with the specified role.

    Args:
        request: The HTTP request object.
        role: The role of the user.

    Returns:
        The rendered registration view or a redirect to the login page.
    """
    role = role.lower()
    try:
        user_level = ROLES[role]
    except KeyError:
        return HttpResponseForbidden("Invalid role.")
    if user_level not in UserType:
        return HttpResponseForbidden("Invalid role.")
    if user_level == UserType.ADMIN:
        return HttpResponseForbidden("Only superusers can register admins.")
    if request.method == "POST":
        form_class = register_user_form_viewer(user_level)
        form = form_class(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_level = user_level
            user.save()
            return redirect("/login")
    else:
        form_class = register_user_form_viewer(user_level)
        form = form_class()
    return render(request, f"register/{role}/index.html", {"form": form})


def login_view(request):
    """
    Handle the login view.

    Args:
        request: The HTTP request object.

    Returns:
        The rendered login view or a redirect to the user's profile page.
    """
    if request.user.is_authenticated:
        return redirect(f'/{request.user.username}/')
    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            user = authenticate(request,
                                username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                return redirect(f'/{user.username}/')
    else:
        form = AuthenticationForm(request=request)
    return render(request, 'login/index.html', {'form': form})


def logout_view(request):
    """
    Handle the logout view.

    Args:
        request: The HTTP request object.

    Returns:
        A redirect to the login page.
    """
    logout(request)
    return redirect('/login/')


@login_required(login_url='/login/')
def profile_view(request, username=None):
    """
    Render the user's profile view.

    Args:
        request: The HTTP request object.
        username: The username of the profile to view.

    Returns:
        The rendered profile view or an HTTP response with an error message.
    """
    user = request.user
    if user.is_staff:
        return redirect('/admin/')
    if not username or username == user.username:
        return render_own_profile(request, user)
    else:
        return render_other_profile(request, user, username)


def render_other_profile(request, user, username):
    """
    Render the profile view for another user.

    Args:
        request: The HTTP request object.
        user: The current user object.
        username: The username of the profile to view.

    Returns:
        The rendered profile view or an HTTP response with an error message.
    """
    profile_user = get_object_or_404(User, username=username)
    if user.user_level == UserType.DOCTOR:
        return render_for_doctor(request, profile_user)
    elif user.user_level == UserType.PATIENT:
        return render_for_patient(request, profile_user)
    else:
        return HttpResponseForbidden("You do not have access to this page.")


def render_for_doctor(request, profile_user):
    """
    Render the profile view for a doctor.

    Args:
        request: The HTTP request object.
        profile_user: The user object of the profile to view.

    Returns:
        The rendered profile view or an HTTP response with an error message.
    """
    if profile_user.user_level == UserType.PATIENT:
        return render_patient_profile_for_doctor(request, profile_user)
    elif profile_user.user_level == UserType.DOCTOR:
        return render_doctor_profile_for_doctor(request, profile_user)
    else:
        return HttpResponseForbidden("You do not have access to this page.")


def render_for_patient(request, profile_user):
    """
    Render the profile view for a patient.

    Args:
        request: The HTTP request object.
        profile_user: The user object of the profile to view.

    Returns:
        The rendered profile view or an HTTP response with an error message.
    """
    if profile_user.user_level == UserType.DOCTOR:
        return render_doctor_profile_for_patient(request, profile_user)
    elif profile_user.user_level == UserType.PATIENT:
        return HttpResponseForbidden("You do not have access to this page.")
    else:
        return HttpResponseForbidden("You do not have access to this page.")


def render_own_profile(request, profile_user):
    """
    Render the user's own profile view.

    Args:
        request: The HTTP request object.
        profile_user: The user object of the profile to view.

    Returns:
        The rendered profile view for the user.
    """
    if profile_user.user_level == UserType.PATIENT:
        diagnoses = Diagnosis.objects.filter(patient=profile_user)
        visits = Visit.objects.filter(patient=profile_user).select_related('doctor')
        visits_info = []
        for visit in visits:
            visits_info.append({
                'doctor': visit.doctor,
                'date': visit.date.strftime('%Y-%m-%d'),
                'start': f"{visit.start.hour:02d}:{visit.start.minute:02d}",
                'end': f"{visit.end.hour:02d}:{visit.end.minute:02d}",
                'status': visit.status,
                'editable': True if visit.status == VisitStatus.ACTIVE else False,
                'id': visit.id
            })
        context = {
            'diagnoses': diagnoses,
            'visits_info': visits_info
        }
        return render(request, 'profile/patient_profile.html', context)
    elif profile_user.user_level == UserType.DOCTOR:
        patients = Visit.objects.filter(
            doctor=profile_user, status=VisitStatus.ACTIVE
        ).select_related('patient')
        schedules = Schedule.objects.filter(doctor=profile_user)
        schedule_info = []
        for schedule in schedules:
            schedule_info.append({
                'doctor': schedule.doctor,
                'start': schedule.start,  # Converts to HH:MM format
                'end': schedule.end,       # Converts to HH:MM format
                'day_of_week': calendar.day_name[int(schedule.day_of_week)],
            })
        future_visits = Visit.objects.filter(doctor=profile_user, date__gt=date.today())
        context = {
            'patients': patients,
            'schedules': schedule_info,
            'future_visits': future_visits
        }
        return render(request, 'profile/doctor_profile.html', context)


def render_patient_profile_for_doctor(request, patient_user):
    """
    Render the patient's profile view for a doctor.

    Args:
        request: The HTTP request object.
        patient_user: The user object of the patient.

    Returns:
        The rendered patient profile view for a doctor.
    """
    diagnoses = Diagnosis.objects.filter(patient=patient_user)
    context = {
        'patient': patient_user,
        'diagnoses': diagnoses
    }
    return render(request, 'profile/patient_profile_for_doctor.html', context)


def render_doctor_profile_for_doctor(request, doctor_user):
    """
    Render the doctor's profile view for a doctor.

    Args:
        request: The HTTP request object.
        doctor_user: The user object of the doctor.

    Returns:
        The rendered doctor profile view for a doctor.
    """
    schedules = Schedule.objects.filter(doctor=doctor_user)
    context = {
        'doctor': doctor_user,
        'schedules': schedules
    }
    return render(request, 'profile/doctor_profile_for_doctor.html', context)


def render_doctor_profile_for_patient(request, doctor_user):
    """
    Render the doctor's profile view for a patient.

    Args:
        request: The HTTP request object.
        doctor_user: The user object of the doctor.

    Returns:
        The rendered doctor profile view for a patient.
    """
    schedules = Schedule.objects.filter(doctor=doctor_user)
    print(request.user, doctor_user)
    if request.method == 'POST':
        form = VisitCreationForm(request.POST, doctor=doctor_user, patient=request.user)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.patient = request.user
            visit.doctor = doctor_user
            visit.save()
            return redirect('profile', username=request.user.username)
    else:
        form = VisitCreationForm(doctor=doctor_user, patient=request.user)

    schedule_info = []
    for schedule in schedules:
        schedule_info.append({
            'doctor': schedule.doctor,
            'start': schedule.start,
            'end': schedule.end,
            'day_of_week': calendar.day_name[int(schedule.day_of_week)],
        })
    context = {
        'doctor': doctor_user,
        'schedules': schedules,
        'form': form
    }
    return render(request, 'profile/doctor_profile_for_patient.html', context)


@login_required(login_url='/login/')
def update_schedule(request, schedule_id: int):
    """
    Update a schedule.

    Args:
        request: The HTTP request object.
        schedule_id: The ID of the schedule to update.

    Returns:
        The rendered update schedule view or a redirect to the user's profile page.
    """
    schedule = get_object_or_404(Schedule, id=schedule_id, doctor=request.user)

    if request.method == 'POST':
        form = ScheduleViewForm(request.POST, instance=schedule)
        form.doctor = request.user
        if form.is_valid():
            form.save()
            return redirect('profile', username=request.user.username)
    else:
        form = ScheduleViewForm(instance=schedule)
        form.doctor = request.user
    return render(request, 'profile/update_schedule.html', {'form': form})


@login_required(login_url='/login/')
def toggle_diagnosis_status(request, diagnosis_id):
    """
    Toggle the status of a diagnosis.

    Args:
        request: The HTTP request object.
        diagnosis_id: The ID of the diagnosis to toggle.

    Returns:
        A redirect to the patient's profile page or an HTTP response with an error message.
    """
    diagnosis = get_object_or_404(Diagnosis, id=diagnosis_id)
    if request.user == diagnosis.doctor:
        diagnosis.is_active = not diagnosis.is_active
        diagnosis.save()
        return redirect(f'/{diagnosis.patient.username}')
    else:
        return HttpResponseForbidden("You do not have access to modify this diagnosis.")


@login_required(login_url='/login/')
def edit_visit(request, visit_id):
    """
    Edit an existing visit.

    Args:
        request: The HTTP request object.
        visit_id: The ID of the visit to edit.

    Returns:
        The rendered edit visit view or a redirect to the user's profile page.
    """
    visit = get_object_or_404(Visit, id=visit_id)
    print(visit_id, visit)
    if request.method == 'POST':
        form = VisitViewForm(request.POST, instance=visit)
        if form.is_valid():
            # Delete the existing visit
            visit.delete()
            # Save the current valid visit
            form.save()
            return redirect(f'/{request.user.username}/')
    else:
        form = VisitViewForm(instance=visit)
    return render(request, 'profile/edit_visit.html', {'form': form})


@login_required(login_url='/login/')
def doctor_schedule(request, doctor_id):
    """
    Render the doctor's schedule view.

    Args:
        request: The HTTP request object.
        doctor_id: The ID of the doctor.

    Returns:
        The rendered doctor schedule view.
    """
    doctor = get_object_or_404(User, id=doctor_id, user_level=UserType.DOCTOR)
    schedule = Schedule.objects.filter(doctor=doctor)
    return render(request,
                  'profile/doctor_schedule.html',
                  {
                      'doctor': doctor,
                      'schedule': schedule
                  })


@login_required(login_url='/login/')
def edit_schedule(request):
    """
    Edit the doctor's schedule.

    Args:
        request: The HTTP request object.

    Returns:
        The rendered edit schedule view or a redirect to the doctor's schedule view.
    """
    if not request.user.is_authenticated or request.user.user_level != UserType.DOCTOR:
        return redirect('home')
    doctor = request.user
    if request.method == 'POST':
        form = ScheduleViewForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('doctor_schedule', doctor_id=doctor.id)
    else:
        form = ScheduleViewForm()
    return render(request, 'profile/edit_schedule.html', {'form': form})


def search_doctors_view(request):
    """
    Render the search doctors view.

    Args:
        request: The HTTP request object.

    Returns:
        The rendered search doctors view.
    """
    filter_form = DoctorSearchForm(request.GET or None)
    doctors = User.objects.none()  # Start with an empty set of doctors

    if request.GET and filter_form.is_valid():
        doctors = User.objects.filter(user_level=UserType.DOCTOR, is_active=True)

        if filter_form.cleaned_data['specialization']:
            doctors = doctors.filter(
                specialty__icontains=filter_form.cleaned_data['specialization']
            )
        if filter_form.cleaned_data['fullname']:
            doctors = doctors.filter(
                Q(fullname__icontains=filter_form.cleaned_data['fullname'])
            )
        if filter_form.cleaned_data['username']:
            doctors = doctors.filter(
                Q(username__icontains=filter_form.cleaned_data['username'])
            )
        if filter_form.cleaned_data['email']:
            doctors = doctors.filter(
                Q(email__icontains=filter_form.cleaned_data['email'])
            )
        if filter_form.cleaned_data['phone']:
            doctors = doctors.filter(
                Q(phone__icontains=filter_form.cleaned_data['phone'])
            )

    context = {
        'doctors': doctors,
        'filter_form': filter_form,
    }

    return render(request, 'search_doctors.html', context)


class VisitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Visit model.
    """
    queryset = Visit.objects.all()
    serializer_class = VisitSerializer
    permission_classes = [IsAuthenticated]


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class DiagnosisViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Diagnosis model.
    """
    queryset = Diagnosis.objects.all()
    serializer_class = DiagnosisSerializer
    permission_classes = [IsAuthenticated]


class ScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Schedule model.
    """
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]
