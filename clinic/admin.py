from django.contrib import admin
from django.core.exceptions import PermissionDenied
from .models import User, Visit, Schedule, Diagnosis, UserType

from .forms import (
    register_user_form_viewer, user_form_viewer,
    AdminVisitCreationForm, AdminVisitViewForm,
    DiagnosisForm, AdminScheduleForm
)

# Constants
LIST_DISPLAY = (
    'username', 'fullname', 'email', 'phone', 'user_level', 'created_at'
)
SEARCH_FIELDS = ('username', 'fullname', 'email', 'phone')
LIST_FILTER = ('user_level', 'created_at')
ORDERING = ('created_at',)


# Admin classes
class UserAdmin(admin.ModelAdmin):
    """
    Admin class for User model.
    """

    list_display = LIST_DISPLAY
    search_fields = SEARCH_FIELDS
    list_filter = LIST_FILTER
    ordering = ORDERING

    def get_form(self, request, obj=None, **kwargs):
        """
        Returns the appropriate form based on the user's role
        and the presence of an object (create/edit).

        Args:
            request (HttpRequest): The current request.
            obj (User, optional): The user object being edited. Defaults to None.

        Returns:
            Form: The appropriate form based on the user's role and the presence of an object.
        """
        if obj is None:  # Creating a new user
            return register_user_form_viewer(request.user.user_level)
        return user_form_viewer(request.user.user_level)

    def delete_model(self, request, obj):
        """
        Deletes a user model instance.
        Raises PermissionDenied if an admin tries to delete a superuser.

        Args:
            request (HttpRequest): The current request.
            obj (User): The user object to be deleted.

        Raises:
            PermissionDenied: If an admin tries to delete a superuser.
        """
        if obj.user_level == UserType.SUPERUSER and \
                request.user.user_level == UserType.ADMIN:
            raise PermissionDenied('Admins cannot delete superusers.')
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """
        Deletes multiple user model instances.
        Raises PermissionDenied if an admin tries to delete a superuser.

        Args:
            request (HttpRequest): The current request.
            queryset (QuerySet): The queryset of user objects to be deleted.

        Raises:
            PermissionDenied: If an admin tries to delete a superuser.
        """
        if queryset.filter(user_level=UserType.SUPERUSER).exists() and \
                request.user.user_level == UserType.ADMIN:
            raise PermissionDenied('Admins cannot delete superusers.')
        super().delete_queryset(request, queryset)

    def save_model(self, request, obj, form, change):
        """
        Saves a user model instance. Sets is_superuser = True,
        is_staff = True for users with ADMIN or SUPERUSER level.

        Args:
            request (HttpRequest): The current request.
            obj (User): The user object to be saved.
            form (Form): The form used to save the user object.
            change (bool): Indicates whether the user object is being edited or created.

        Returns:
            None
        """
        if request.user.user_level == UserType.ADMIN and obj.user_level == UserType.SUPERUSER:
            raise PermissionDenied('Admins cannot create superusers.')
        if obj.user_level in [UserType.ADMIN, UserType.SUPERUSER]:
            obj.is_superuser = True
            obj.is_staff = True
        super().save_model(request, obj, form, change)


class VisitAdmin(admin.ModelAdmin):
    """
    Admin class for Visit model.
    """
    list_display = ('patient', 'doctor', 'start', 'end', 'status')
    search_fields = ('patient__fullname', 'doctor__fullname', 'status')
    list_filter = ('status', 'start', 'end')
    ordering = ('start',)

    def get_form(self, request, obj=None, **kwargs):
        """
        Returns the appropriate form based on the presence of an object (create/edit).

        Parameters:
            request (HttpRequest): The request object.
            obj (object, optional): The object being edited. Defaults to None.
            **kwargs: Additional keyword arguments.

        Returns:
            form (Form): The appropriate form based on the presence of an object.
        """
        if obj is None:
            return AdminVisitCreationForm
        return AdminVisitViewForm


class ScheduleAdmin(admin.ModelAdmin):
    """
    Admin class for Schedule model.
    """
    form = AdminScheduleForm
    list_display = ('doctor', 'day_of_week', 'start', 'end')
    search_fields = ('doctor__fullname', 'day_of_week')
    list_filter = ('day_of_week', 'doctor')
    ordering = ('doctor', 'day_of_week')


class DiagnosisAdmin(admin.ModelAdmin):
    """
    Admin class for Diagnosis model.
    """
    form = DiagnosisForm
    list_display = ('patient', 'doctor', 'description', 'is_active')
    search_fields = ('patient__fullname', 'doctor__fullname', 'description')
    list_filter = ('is_active',)
    ordering = ('patient', 'doctor')


admin.site.register(User, UserAdmin)
admin.site.register(Visit, VisitAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Diagnosis, DiagnosisAdmin)
