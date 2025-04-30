from django.contrib import admin
from .models import (Session,
                     Student, 
                     Course, 
                     Enrollment,
                     Assessment, 
                     AssessmentType, 
                     Attendance, 
                     Certificate,
                     )

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """ Класс для отображения в админке модели Session """
    list_display = ("session_number",)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """ Класс для отображения в админке модели Student """
    list_display = ('full_name',
                    'email',
                    'start_date',
                    'status',
                    )
    search_fields = ('full_name',
                     'email')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """ Класс для отображения в админке модели Course """
    list_display = ('title',
                    'description',
                    'session',
                    )
    list_filter = ('title', "session")

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """ Класс для отображения в админке модели Entrollment """
    list_display = (
        'student',
        'course',
        'status',
        'enrolled_on')
    list_filter = ('status',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """ Класс для отображения в админке модели Attendance """
    list_display = (
        "enrollment",
        "session",
        "present",
    )

@admin.register(AssessmentType)
class AssessmentTypeAdmin(admin.ModelAdmin):
    """ Класс для отображения в админке модели AssessmentType """
    list_display = ("name",)

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    """ Модель для отображения в админке модели Assessment """
    list_display = (
        "enrollment",
        "type",
        "score",
        "date",
        "certificate_issued",
    )

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """ Модель для отображения в админке модели Certificate """
    list_display = (
        "assessment",
        "issued_on",
        "file",
    )

