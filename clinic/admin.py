from django.contrib import admin
from django.core.exceptions import PermissionDenied
from .models import User, Visit, Schedule, Diagnosis, UserType
from .forms import (
    register_user_form_viewer, user_form_viewer,
    VisitCreationForm, VisitViewForm, DiagnosisForm, AdminScheduleForm
)

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'fullname', 'email', 'phone', 'user_level', 'created_at')
    search_fields = ('username', 'fullname', 'email', 'phone')
    list_filter = ('user_level', 'created_at')
    ordering = ('created_at',)

    def get_form(self, request, obj=None, **kwargs):
        # Определяем форму в зависимости от роли пользователя и наличия объекта (создание/редактирование)
        if obj is None:  # Это создание нового пользователя
            return register_user_form_viewer(request.user.user_level)
        return user_form_viewer(request.user.user_level)

    def delete_model(self, request, obj):
        if obj.user_level == UserType.SUPERUSER and request.user.user_level == UserType.ADMIN:
            raise PermissionDenied('Admins cannot delete superusers.')
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        if queryset.filter(user_level=UserType.SUPERUSER).exists() and request.user.user_level == UserType.ADMIN:
            raise PermissionDenied('Admins cannot delete superusers.')
        super().delete_queryset(request, queryset)
    
    def save_model(self, request, obj, form, change):
        # Устанавливаем is_superuser = True, is_staff = True для пользователей с уровнем ADMIN или SUPERUSER
        if obj.user_level in [UserType.ADMIN, UserType.SUPERUSER]:
            obj.is_superuser = True
            obj.is_staff = True
        super().save_model(request, obj, form, change)

class VisitAdmin(admin.ModelAdmin):
    # form = VisitForm
    list_display = ('patient', 'doctor', 'start', 'end', 'status')
    search_fields = ('patient__fullname', 'doctor__fullname', 'status')
    list_filter = ('status', 'start', 'end')
    ordering = ('start',)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            return VisitCreationForm
        return VisitViewForm

class ScheduleAdmin(admin.ModelAdmin):
    form = AdminScheduleForm
    list_display = ('doctor', 'day_of_week', 'start', 'end')
    search_fields = ('doctor__fullname', 'day_of_week')
    list_filter = ('day_of_week', 'doctor')
    ordering = ('doctor', 'day_of_week')

class DiagnosisAdmin(admin.ModelAdmin):
    form = DiagnosisForm
    list_display = ('patient', 'doctor', 'description', 'is_active')
    search_fields = ('patient__fullname', 'doctor__fullname', 'description')
    list_filter = ('is_active',)
    ordering = ('patient', 'doctor')

admin.site.register(User, UserAdmin)
admin.site.register(Visit, VisitAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Diagnosis, DiagnosisAdmin)
