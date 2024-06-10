from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from .forms import (
    register_user_form_viewer,
    VisitForm, ScheduleViewForm, VisitViewForm, VisitCreationForm,
    DoctorSearchForm
)
import calendar
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from .models import User, Visit, Schedule, Diagnosis, UserType, VisitStatus
from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import UserSerializer, VisitSerializer, ScheduleSerializer, DiagnosisSerializer
from datetime import date


ROLES = {'patient': 0, 'doctor': 1, 'admin': 2, 'superuser': 3}


def main_page_view(request):
    return render(request, 'base_generic.html')

def register_choose_view(request):
    return render(request, 'register/index.html')


def convert(number: int) -> str:
    """Convert number to time using 24 hours format. Example: convert(1) -> '00:15'

    Args:
        number (int): _description_

    Returns:
        str: _description_
    """
    if 0 <= number <= 96:
        hours = number // 4
        minutes = (number % 4) * 15
        return f"{hours:02}:{minutes:02}"
    else:
        return "Неверное число. Введите значение от 0 до 96."


def convert_to_number(time_str: str) -> int:
    try:
        hours, minutes = map(int, time_str.split(":"))
        if 0 <= hours < 24 and 0 <= minutes < 60:
            return (hours * 4) + (minutes // 15)
        else:
            return -1  # Неверное время
    except ValueError:
        return -1  # Неверный формат времени


def register(request, role: str):
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
    if request.user.is_authenticated:
        return redirect(f'/{request.user.username}/')
    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                return redirect(f'/{user.username}/')
    else:
        form = AuthenticationForm(request=request)
    return render(request, 'login/index.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('/login/')

@login_required(login_url='/login/')
def profile_view(request, username=None):
    user = request.user
    if user.is_staff:
        return redirect('/admin/')
    if not username or username == user.username:
        profile_user = user
        return render_own_profile(request, profile_user)
    else:
        profile_user = get_object_or_404(User, username=username)
        if user.user_level == UserType.DOCTOR:
            if profile_user.user_level == UserType.PATIENT:
                return render_patient_profile_for_doctor(request, profile_user)
            elif profile_user.user_level == UserType.DOCTOR:
                return render_doctor_profile_for_doctor(request, profile_user)
        elif user.user_level == UserType.PATIENT:
            if profile_user.user_level == UserType.DOCTOR:
                return render_doctor_profile_for_patient(request, profile_user)
            elif profile_user.user_level == UserType.PATIENT:
                return HttpResponseForbidden("You do not have access to this page.")
    return HttpResponseForbidden("You do not have access to this page.")

def render_own_profile(request, profile_user):
    if profile_user.user_level == UserType.PATIENT:
        diagnoses = Diagnosis.objects.filter(patient=profile_user)
        visits = Visit.objects.filter(patient=profile_user).select_related('doctor')
        visits_info = []
        for visit in visits:
            visits_info.append({
                'doctor': visit.doctor,
                'date': visit.date.strftime('%d.%m.%Y'),
                'start': f"{(visit.start // 4):02d}:{(visit.start % 4) * 15:02d}",  # Converts to HH:MM format
                'end': f"{(visit.end // 4):02d}:{(visit.end % 4) * 15:02d}",       # Converts to HH:MM format
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
        patients = Visit.objects.filter(doctor=profile_user, status=VisitStatus.ACTIVE).select_related('patient')
        schedules = Schedule.objects.filter(doctor=profile_user)
        schedule_info = []
        for schedule in schedules:
            schedule_info.append({
                'doctor': schedule.doctor,
                'start': convert(schedule.start),  # Converts to HH:MM format
                'end': convert(schedule.end),       # Converts to HH:MM format
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
    diagnoses = Diagnosis.objects.filter(patient=patient_user)
    context = {
        'patient': patient_user,
        'diagnoses': diagnoses
    }
    return render(request, 'profile/patient_profile_for_doctor.html', context)

def render_doctor_profile_for_doctor(request, doctor_user):
    schedules = Schedule.objects.filter(doctor=doctor_user)
    context = {
        'doctor': doctor_user,
        'schedules': schedules
    }
    return render(request, 'profile/doctor_profile_for_doctor.html', context)

def render_doctor_profile_for_patient(request, doctor_user):
    schedules = Schedule.objects.filter(doctor=doctor_user)
    if request.method == 'POST':
        form = VisitCreationForm(request.POST)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.patient = request.user
            visit.doctor = doctor_user
            visit.save()
            return redirect('profile', username=request.user.username)
    else:
        form = VisitViewForm

    schedule_info = []
    for schedule in schedules:
        schedule_info.append({
            'doctor': schedule.doctor,
            'start': convert(schedule.start),  # Converts to HH:MM format
            'end': convert(schedule.end),       # Converts to HH:MM format
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
    diagnosis = get_object_or_404(Diagnosis, id=diagnosis_id)
    if request.user == diagnosis.doctor:
        diagnosis.is_active = not diagnosis.is_active
        diagnosis.save()
        return redirect(f'/{diagnosis.patient.username}')
    else:
        return HttpResponseForbidden("You do not have access to modify this diagnosis.")


@login_required(login_url='/login/')
def create_visit(request):
    if request.method == 'POST':
        form = VisitCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(f'/{request.user.username}/')
    else:
        form = VisitCreationForm
    return render(request, 'profile/create_visit.html', {'form': form})

@login_required(login_url='/login/')
def edit_visit(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id)
    if request.method == 'POST':
        form = VisitViewForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            return redirect(f'/{request.user.username}/')
    else:
        form = VisitViewForm(instance=visit)
    return render(request, 'profile/edit_visit.html', {'form': form})

@login_required(login_url='/login/')
def doctor_schedule(request, doctor_id):
    doctor = get_object_or_404(User, id=doctor_id, user_level=UserType.DOCTOR)
    schedule = Schedule.objects.filter(doctor=doctor)
    return render(request, 'profile/doctor_schedule.html', {'doctor': doctor, 'schedule': schedule})

@login_required(login_url='/login/')
def edit_schedule(request):
    if not request.user.is_doctor:
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

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.all()
    serializer_class = VisitSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        doctor = get_object_or_404(User, id=data.get("doctor"), user_level=UserType.DOCTOR)
        patient = get_object_or_404(User, id=data.get("patient"), user_level=UserType.PATIENT)
        
        if doctor == patient:
            return Response({"error": "Doctor cannot have a visit with themselves."}, status=status.HTTP_400_BAD_REQUEST)
        if not doctor.is_active:
            return Response({"error": "The doctor is not active."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = VisitSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()

def search_doctors_view(request):
    filter_form = DoctorSearchForm(request.GET or None)
    doctors = User.objects.none()  # Начинаем с пустого набора докторов
    
    if request.GET and filter_form.is_valid():  # Проверяем, были ли отправлены данные через GET-запрос и является ли форма валидной
        doctors = User.objects.filter(user_level=UserType.DOCTOR, is_active=True)
        
        if filter_form.cleaned_data['specialization']:
            doctors = doctors.filter(specialty__icontains=filter_form.cleaned_data['specialization'])
        if filter_form.cleaned_data['fullname']:
            doctors = doctors.filter(Q(fullname__icontains=filter_form.cleaned_data['fullname']))
        if filter_form.cleaned_data['username']:
            doctors = doctors.filter(Q(username__icontains=filter_form.cleaned_data['username']))
        if filter_form.cleaned_data['email']:
            doctors = doctors.filter(Q(email__icontains=filter_form.cleaned_data['email']))
        if filter_form.cleaned_data['phone']:
            doctors = doctors.filter(Q(phone__icontains=filter_form.cleaned_data['phone']))

    context = {
        'doctors': doctors,
        'filter_form': filter_form,
    }
    
    return render(request, 'search_doctors.html', context)

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer

class DiagnosisViewSet(viewsets.ModelViewSet):
    queryset = Diagnosis.objects.all()
    serializer_class = DiagnosisSerializer
