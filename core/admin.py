from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.db.models import Count, Avg, Prefetch, Q
from django.db import connection
import logging

from .models import (Session,
                     Student, 
                     Course, 
                     Enrollment,
                     Assessment, 
                     AssessmentType, 
                     Attendance, 
                     Certificate,
                     Statistic,
                     )

logger = logging.getLogger('core')

class OptimizedMixin:
    """Миксин для оптимизации админки"""
    
    def get_queryset(self, request):
        """Оптимизируем запросы для списка объектов"""
        qs = super().get_queryset(request)
        if hasattr(self, 'optimize_queryset'):
            return self.optimize_queryset(qs)
        return qs

class AttendanceInline(admin.TabularInline):
    """ Inline класс для записей о посещаемости """
    model = Attendance
    extra = 0
    readonly_fields = ('session', 'present')
    verbose_name = "Посещаемость"
    verbose_name_plural = "Записи о посещаемости"
    can_delete = False
    show_change_link = False
    max_num = 10  # Ограничиваем количество
    
    def has_add_permission(self, request, obj=None):
        return False

class AssessmentInline(admin.TabularInline):
    """ Inline класс для оценок """
    model = Assessment
    extra = 0
    readonly_fields = ('course', 'type', 'score', 'date', 'is_final_grade')
    verbose_name = "Оценка"
    verbose_name_plural = "Оценки"
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

class CertificateInline(admin.TabularInline):
    """ Inline класс для сертификатов """
    model = Certificate
    extra = 0
    readonly_fields = ('course', 'type', 'issued_on', 'get_assessment_score')
    verbose_name = "Сертификат"
    verbose_name_plural = "Сертификаты"
    can_delete = False
    show_change_link = False
    max_num = 15  # Ограничиваем количество
    
    def get_assessment_score(self, obj):
        if obj.assessment:
            return f"{obj.assessment.score}"
        return "—"
    get_assessment_score.short_description = 'Балл'
    
    def has_add_permission(self, request, obj=None):
        return False

class EnrollmentInline(admin.TabularInline):
    """ Inline класс для записей о зачислении """
    model = Enrollment
    extra = 0
    readonly_fields = ('session', 'status', 'enrolled_on')
    verbose_name = "Зачисление"
    verbose_name_plural = "Записи о зачислении"
    can_delete = False
    show_change_link = False
    max_num = 10  # Ограничиваем количество
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Session)
class SessionAdmin(OptimizedMixin, admin.ModelAdmin):
    """ Класс для отображения в админке модели Session """
    list_display = ("session_number", "get_courses_count", "get_students_count")
    ordering = ("session_number",)
    list_per_page = 50
    
    def optimize_queryset(self, qs):
        return qs.prefetch_related('courses', 'enrollments__student')
    
    def get_courses_count(self, obj):
        # Используем кэш или аннотацию
        if hasattr(obj, 'courses_count'):
            return obj.courses_count
        return obj.courses.count()
    get_courses_count.short_description = 'Предметов'
    
    def get_students_count(self, obj):
        # Используем кэш или аннотацию
        if hasattr(obj, 'students_count'):
            return obj.students_count
        return obj.enrollments.values('student').distinct().count()
    get_students_count.short_description = 'Студентов'

@admin.register(Student)
class StudentAdmin(OptimizedMixin, admin.ModelAdmin):
    """ Класс для отображения в админке модели Student """
    list_display = ('full_name',
                    'email',
                    'status',
                    'get_sessions_count',
                    'get_certificates_count',
                    'get_total_score')
    search_fields = ('full_name', 'email')
    list_filter = ('status',)
    inlines = []  # Убираю inline для ускорения загрузки
    list_per_page = 20  # Еще меньше записей на странице
    readonly_fields = ('get_quick_stats',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('full_name', 'email', 'status')
        }),
        ('Быстрая статистика', {
            'fields': ('get_quick_stats',),
        }),
    )
    
    def optimize_queryset(self, qs):
        """Минимальная оптимизация для списка студентов"""
        return qs.select_related('statistic').annotate(
            sessions_count=Count('enrollments__session', distinct=True),
            certificates_count=Count('certificates', distinct=True)
        )
    
    def get_sessions_count(self, obj):
        if hasattr(obj, 'sessions_count'):
            return obj.sessions_count
        return obj.enrollments.values('session').distinct().count()
    get_sessions_count.short_description = 'Сессий'
    
    def get_certificates_count(self, obj):
        if hasattr(obj, 'certificates_count'):
            return obj.certificates_count
        return obj.certificates.count()
    get_certificates_count.short_description = 'Сертификатов'
    
    def get_total_score(self, obj):
        """Быстрый подсчет среднего балла"""
        cache_key = f"student_avg_score_{obj.id}"
        avg_score = cache.get(cache_key)
        
        if avg_score is None:
            # Самый быстрый запрос для среднего балла
            scores = Assessment.objects.filter(
                enrollment__student=obj, 
                is_final_grade=True
            ).values_list('score', flat=True)
            
            if scores:
                avg_score = sum(float(score) for score in scores) / len(scores)
                cache.set(cache_key, avg_score, 600)  # Кэш на 10 минут
            else:
                avg_score = 0
        
        return f"{avg_score:.1f}" if avg_score > 0 else "—"
    get_total_score.short_description = 'Средний балл'
    
    def get_quick_stats(self, obj):
        """Быстрая статистика без детализации"""
        cache_key = f"student_quick_stats_{obj.id}"
        html_content = cache.get(cache_key)
        
        if html_content is None:
            try:
                stat = obj.statistic
                html_content = format_html(
                    """
                    <div style="background: var(--body-bg, #f8f9fa); border: 1px solid var(--border-color, #dee2e6); padding: 12px; border-radius: 6px; font-size: 14px; color: var(--body-fg, #333);">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
                            <div>📚 Прослушано: <strong>{}</strong></div>
                            <div>✅ Освидетельствовано: <strong style="color: #28a745;">{}</strong></div>
                            <div>❌ Не освидетельствовано: <strong style="color: #dc3545;">{}</strong></div>
                            <div>📅 Посещено сессий: <strong>{}</strong></div>
                        </div>
                        <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border-color, #dee2e6); color: var(--body-quiet-color, #6c757d); text-align: center;">
                            <a href="/admin/core/enrollment/?q={}" target="_blank" style="margin-right: 10px; color: var(--link-fg, #0066cc);">📝 Зачисления</a>
                            <a href="/admin/core/certificate/?q={}" target="_blank" style="margin-right: 10px; color: var(--link-fg, #0066cc);">🏆 Сертификаты</a>
                            <a href="/admin/core/assessment/?q={}" target="_blank" style="color: var(--link-fg, #0066cc);">📊 Оценки</a>
                        </div>
                    </div>
                    """,
                    stat.total_courses,
                    stat.certified,
                    stat.uncertified,
                    stat.sessions_attended,
                    obj.full_name,
                    obj.full_name,
                    obj.full_name
                )
                cache.set(cache_key, html_content, 900)  # Кэш на 15 минут
            except Statistic.DoesNotExist:
                html_content = format_html(
                    """
                    <div style='color: #6c757d; text-align: center; padding: 20px;'>
                        Статистика не рассчитана<br>
                        <a href="/admin/core/enrollment/?q={}" target="_blank" style="margin-right: 10px;">📝 Зачисления</a>
                        <a href="/admin/core/certificate/?q={}" target="_blank">🏆 Сертификаты</a>
                    </div>
                    """,
                    obj.id,
                    obj.full_name
                )
                cache.set(cache_key, html_content, 300)
        
        return mark_safe(html_content)
    get_quick_stats.short_description = 'Статистика и ссылки'

@admin.register(Course)
class CourseAdmin(OptimizedMixin, admin.ModelAdmin):
    """ Класс для отображения в админке модели Course """
    list_display = ('title',
                    'session',
                    'get_students_count',
                    'get_avg_score',
                    'description',
                    )
    list_filter = ('session',)
    search_fields = ('title',)
    ordering = ('session__session_number', 'title')
    list_per_page = 50
    
    def optimize_queryset(self, qs):
        return qs.select_related('session').prefetch_related('assessments__enrollment__student')
    
    def get_students_count(self, obj):
        cache_key = f"course_students_{obj.id}"
        count = cache.get(cache_key)
        if count is None:
            count = obj.assessments.values('enrollment__student').distinct().count()
            cache.set(cache_key, count, 300)
        return count
    get_students_count.short_description = 'Студентов'
    
    def get_avg_score(self, obj):
        cache_key = f"course_avg_{obj.id}"
        avg = cache.get(cache_key)
        if avg is None:
            final_assessments = obj.assessments.filter(is_final_grade=True)
            if final_assessments.exists():
                avg = sum(float(a.score) for a in final_assessments) / final_assessments.count()
                cache.set(cache_key, avg, 300)
            else:
                avg = 0
        return f"{avg:.1f}" if avg > 0 else "—"
    get_avg_score.short_description = 'Средний балл'

@admin.register(Enrollment)
class EnrollmentAdmin(OptimizedMixin, admin.ModelAdmin):
    """ Класс для отображения в админке модели Enrollment """
    list_display = (
        'get_student_name',
        'get_session_number',
        'status',
        'enrolled_on',
        'get_attendance_status')
    list_filter = ('status', 'session')
    search_fields = ('student__full_name',)
    date_hierarchy = "enrolled_on"
    list_per_page = 50
    
    def optimize_queryset(self, qs):
        return qs.select_related('student', 'session').prefetch_related('attendances')
    
    def get_student_name(self, obj):
        return obj.student.full_name
    get_student_name.short_description = 'Студент'
    
    def get_session_number(self, obj):
        return f"№{obj.session.session_number}"
    get_session_number.short_description = 'Сессия'
    
    def get_attendance_status(self, obj):
        attendance = obj.attendances.first()
        if attendance:
            return "✅" if attendance.present else "❌"
        return "?"
    get_attendance_status.short_description = 'Присутствие'

@admin.register(Attendance)
class AttendanceAdmin(OptimizedMixin, admin.ModelAdmin):
    """ Класс для отображения в админке модели Attendance """
    list_display = (
        "get_student_name",
        "get_session_number",
        "present",
    )
    list_filter = ("present", "session")
    search_fields = ("enrollment__student__full_name",)
    list_per_page = 100
    
    def optimize_queryset(self, qs):
        return qs.select_related('enrollment__student', 'session')
    
    def get_student_name(self, obj):
        return obj.enrollment.student.full_name
    get_student_name.short_description = 'Студент'
    
    def get_session_number(self, obj):
        return f"№{obj.session.session_number}"
    get_session_number.short_description = 'Сессия'

@admin.register(AssessmentType)
class AssessmentTypeAdmin(OptimizedMixin, admin.ModelAdmin):
    """ Класс для отображения в админке модели AssessmentType """
    list_display = ("name", "weight", "get_assessments_count")
    ordering = ("name",)
    list_per_page = 50
    
    def get_assessments_count(self, obj):
        cache_key = f"assessment_type_count_{obj.id}"
        count = cache.get(cache_key)
        if count is None:
            count = obj.assessments.count()
            cache.set(cache_key, count, 600)
        return count
    get_assessments_count.short_description = 'Оценок'

@admin.register(Assessment)
class AssessmentAdmin(OptimizedMixin, admin.ModelAdmin):
    """ Модель для отображения в админке модели Assessment """
    list_display = (
        "get_student_name",
        "course",
        "type",
        "score",
        "date",
        "is_final_grade",
    )
    list_filter = ("course", "type", "date", "is_final_grade", "enrollment__student")
    search_fields = ("enrollment__student__full_name", "course__title")
    date_hierarchy = "date"
    list_per_page = 100
    
    def optimize_queryset(self, qs):
        return qs.select_related('enrollment__student', 'course', 'type')
    
    def get_student_name(self, obj):
        return obj.enrollment.student.full_name
    get_student_name.short_description = 'Студент'

@admin.register(Certificate)
class CertificateAdmin(OptimizedMixin, admin.ModelAdmin):
    """ Модель для отображения в админке модели Certificate """
    list_display = (
        "student",
        "course",
        "type",
        "issued_on",
        "get_assessment_score"
    )
    list_filter = ("type", "course__session", "issued_on")
    search_fields = ("student__full_name", "course__title")
    date_hierarchy = "issued_on"
    list_per_page = 100
    
    def optimize_queryset(self, qs):
        return qs.select_related('student', 'course__session', 'assessment__type')
    
    def get_assessment_score(self, obj):
        if obj.assessment:
            return f"{obj.assessment.score}"
        return "—"
    get_assessment_score.short_description = 'Балл'

@admin.register(Statistic)
class StatisticAdmin(OptimizedMixin, admin.ModelAdmin):
    """ Модель для отображения в админке модели Statistic """
    list_display = (
        "student",
        "total_courses",
        "certified", 
        "uncertified",
        "sessions_attended",
        "sessions_missed",
        "get_completion_percentage"
    )
    search_fields = ("student__full_name",)
    list_filter = ("sessions_attended", "sessions_missed")
    readonly_fields = ("student",)
    list_per_page = 100
    
    def optimize_queryset(self, qs):
        return qs.select_related('student')
    
    def get_completion_percentage(self, obj):
        if obj.total_courses > 0:
            percentage = (obj.certified / obj.total_courses) * 100
            return f"{percentage:.1f}%"
        return "0%"
    get_completion_percentage.short_description = '% завершения'

