from rest_framework import serializers
from .models import User, Visit, Schedule, Diagnosis


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class ScheduleSerializer(serializers.ModelSerializer):
    start = serializers.TimeField(format='%H:%M')
    end = serializers.TimeField(format='%H:%M')

    class Meta:
        model = Schedule
        fields = '__all__'

class VisitSerializer(serializers.ModelSerializer):
    start = serializers.TimeField(format='%H:%M')
    end = serializers.TimeField(format='%H:%M')

    class Meta:
        model = Visit
        fields = '__all__'

class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = '__all__'
