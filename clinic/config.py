# Constants
WORK_DAY_DURATION_LIMIT = 7200  # 2 hours

# Error messages
ERROR_MESSAGES = {
    'empty_fullname': "Fullname can't be empty.",
    'contains_numbers': "Fullname can't contain numbers.",
    'invalid_fullname': "Fullname must contain 2 words.",
    'future_dob': "Date of birth cannot be in the future.",
    'invalid_phone': "Phone number must contain only digits.",
    'empty_email': "Email cannot be empty.",
    'invalid_username': "Username invalid. Try another username.",
    'invalid_user_level': "This type of user doesn't exist",
    'invalid_specialty': "Specialty is not allowed for this type of user.",
    'required_specialty': "Specialty is required for doctors.",
    'invalid_specialty_letters': "Specialty must contain only letters.",
    'invalid_start_end_time': "Start time must be before end time.",
    'exceeded_work_day_duration': "The duration of the work day cannot exceed 2 hours.",
    'invalid_time_format': "Invalid time format.",
    'overlapping_visit': "The doctor already has a visit scheduled during this time.",
    'outside_schedule': "The visit is outside the doctor's schedule.",
    'invalid_visit_status': "A future visit cannot have the status 'Visited' or 'Missed'.",
    'invalid_past_visit_status': "A past visit cannot have the status 'Scheduled'.",
    'required_doctor_patient': "Both doctor and patient must have a user account.",
    'doctor_self_visit': "Doctor cannot have a visit with themselves.",
    'inactive_doctor': "The doctor is not active.",
    'invalid_description': "Description is required.",
    'short_description': "Description must be more detailed.",
    'invalid_schedule_overlap': "This schedule overlaps with an existing schedule for the doctor.",
    'invalid_time_increment': "Both start and end times must be in 15-minute increments.",
    'search_params_required': "Please enter at least one parameter for search.",
    'doctor_patient_required': 'Doctor and patient are required.',
    'doctor_level': 'The assigned doctor must have the Doctor user level.',
    'patient_level': 'The assigned patient must have the Patient user level.',
    'doctor_inactive': 'The doctor is not active.',
    'description_required': 'Description is required.',
    'description_detailed': 'Description must be more detailed.',
    'doctor_assigned': 'Doctor must be assigned.',
    'schedule_overlap': 'This schedule overlaps with an existing schedule for the doctor.',
    'time_increments': 'Both start and end times must be in 15-minute increments.',
    'phone_digits': 'Phone number must contain only digits.',
    'username_invalid': 'Username invalid. Try another username.',
    'fullname_numbers': "Fullname can't contain numbers.",
    'fullname_two_words': 'Fullname must contain 2 words.',
    'search_param_required': 'Please enter at least one parameter for search.',
}

# start and end attrs
START_END_ATTRS = {'type': 'time', 'step': 900, 'min': '00:00', 'max': '23:45'}

STATUS_ACTIVE = 'Active'

WEEKDAYS_CHOICES = [
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday'),
]

START_END_ATTRS = {'class': 'time-picker',
                   'placeholder': 'HH:MM',
                   'type': 'time',
                   'step': 900,
                   'min': '00:00',
                   'max': '23:45'}

SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']
