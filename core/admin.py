from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
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

class AttendanceInline(admin.TabularInline):
    """ Inline класс для записей о посещаемости """
    model = Attendance
    extra = 0
    readonly_fields = ('session', 'present')
    verbose_name = "Посещаемость"
    verbose_name_plural = "Записи о посещаемости"
    can_delete = False
    
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
    
    def get_assessment_score(self, obj):
        if obj.assessment:
            return f"{obj.assessment.score} ({obj.assessment.type.name})"
        return "Нет связанной оценки"
    get_assessment_score.short_description = 'Связанная оценка'
    
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
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """ Класс для отображения в админке модели Session """
    list_display = ("session_number", "get_courses_count", "get_students_count")
    ordering = ("session_number",)
    
    def get_courses_count(self, obj):
        return obj.courses.count()
    get_courses_count.short_description = 'Количество предметов'
    
    def get_students_count(self, obj):
        return obj.enrollments.values('student').distinct().count()
    get_students_count.short_description = 'Количество студентов'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """ Класс для отображения в админке модели Student """
    list_display = ('full_name',
                    'email',
                    'status',
                    'get_sessions_count',
                    'get_certificates_count',
                    'get_total_score')
    search_fields = ('full_name', 'email')
    list_filter = ('status',)
    inlines = [EnrollmentInline, CertificateInline]
    list_per_page = 20
    readonly_fields = ('get_detailed_progress', 'get_statistic_info')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('full_name', 'email', 'status')
        }),
        ('Статистика обучения', {
            'fields': ('get_statistic_info', 'get_detailed_progress'),
            'classes': ('wide',)
        }),
    )
    
    def get_sessions_count(self, obj):
        return obj.enrollments.values('session').distinct().count()
    get_sessions_count.short_description = 'Сессий'
    
    def get_certificates_count(self, obj):
        return obj.certificates.count()
    get_certificates_count.short_description = 'Сертификатов'
    
    def get_total_score(self, obj):
        total_assessments = obj.enrollments.prefetch_related('assessments').all()
        total_score = 0
        count = 0
        for enrollment in total_assessments:
            for assessment in enrollment.assessments.filter(is_final_grade=True):
                total_score += float(assessment.score)
                count += 1
        return f"{total_score/count:.1f}" if count > 0 else "Нет оценок"
    get_total_score.short_description = 'Средний балл'
    
    def get_statistic_info(self, obj):
        try:
            stat = obj.statistic
            return format_html(
                """
                <link rel="stylesheet" type="text/css" href="/static/core/admin/css/dark-theme.css">
                <div class="student-statistics" style="background: var(--body-bg, #f8f9fa); 
                           color: var(--body-fg, #333); 
                           padding: 10px; 
                           border-radius: 5px; 
                           border: 1px solid var(--border-color, #ddd);">
                    <strong>Персональная успеваемость:</strong><br>
                    <span class="emoji">📚</span> Прослушано предметов: <strong style="color: var(--link-fg, #007bff);">{}</strong><br>
                    <span class="emoji">✅</span> Освидетельствовано: <strong style="color: var(--success-fg, #28a745);">{}</strong><br>
                    <span class="emoji">❌</span> Не освидетельствовано: <strong style="color: var(--error-fg, #dc3545);">{}</strong><br>
                    <span class="emoji">📅</span> Посещено сессий: <strong style="color: var(--link-fg, #007bff);">{}</strong><br>
                    <span class="emoji">⚠️</span> Пропущено сессий: <strong style="color: var(--warning-fg, #ffc107);">{}</strong><br>
                    <span class="emoji">⏰</span> Опоздание на сессий: <strong style="color: var(--warning-fg, #ffc107);">{}</strong>
                </div>
                """,
                stat.total_courses,
                stat.certified,
                stat.uncertified,
                stat.sessions_attended,
                stat.sessions_missed,
                stat.sessions_late
            )
        except Statistic.DoesNotExist:
            return "Статистика не рассчитана"
    get_statistic_info.short_description = 'Статистика'
    
    def get_detailed_progress(self, obj):
        # Группируем оценки по сессиям и курсам
        enrollments = obj.enrollments.select_related('session').prefetch_related(
            'assessments__course', 'assessments__type', 'attendances'
        ).order_by('session__session_number')
        
        html_parts = []
        
        for enrollment in enrollments:
            session = enrollment.session
            # Проверяем посещаемость
            attendance = enrollment.attendances.filter(session=session).first()
            attendance_status = "✅ Присутствовал" if attendance and attendance.present else "❌ Отсутствовал"
            
            html_parts.append(f"""
                <div class="session-progress" style="margin-bottom: 15px; 
                           border: 1px solid var(--border-color, #ddd); 
                           padding: 10px; 
                           border-radius: 5px;
                           background: var(--body-bg, #fff);
                           color: var(--body-fg, #333);">
                    <h4 style="margin: 0 0 10px 0; color: var(--body-fg, #333);">
                        <span class="emoji">📚</span> Сессия №{session.session_number} - {attendance_status}
                    </h4>
            """)
            
            # Группируем оценки по курсам
            courses_assessments = {}
            for assessment in enrollment.assessments.all():
                course = assessment.course
                if course not in courses_assessments:
                    courses_assessments[course] = []
                courses_assessments[course].append(assessment)
            
            if courses_assessments:
                for course, assessments in courses_assessments.items():
                    html_parts.append(f"""
                        <div style="margin-left: 20px; margin-bottom: 10px;">
                            <strong style="color: var(--body-fg, #333);"><span class="emoji">📖</span> {course.title}:</strong><br>
                    """)
                    
                    # Показываем все оценки по курсу
                    final_grade = None
                    regular_assessments = []
                    
                    for assessment in assessments:
                        if assessment.is_final_grade:
                            final_grade = assessment
                        else:
                            regular_assessments.append(assessment)
                    
                    # Обычные оценки
                    if regular_assessments:
                        html_parts.append('<div style="margin-left: 20px;">')
                        for assessment in regular_assessments:
                            html_parts.append(f"""
                                <span style="color: var(--body-fg, #666);">• {assessment.type.name}: 
                                <strong style="color: var(--link-fg, #007bff);">{assessment.score}</strong></span><br>
                            """)
                        html_parts.append('</div>')
                    
                    # Итоговая оценка
                    if final_grade:
                        html_parts.append(f"""
                            <div style="margin-left: 20px; 
                                       background: var(--success-bg, #e8f5e8); 
                                       color: var(--success-fg, #155724);
                                       padding: 5px; 
                                       border-radius: 3px;
                                       border: 1px solid var(--success-border, #c3e6cb);">
                                <span class="emoji">🎯</span> <strong>Итоговая оценка: {final_grade.score}</strong>
                            </div>
                        """)
                    
                    # Информация о сертификате
                    certificate = obj.certificates.filter(course=course).first()
                    if certificate:
                        # Цвета для темной и светлой темы
                        status_colors = {
                            'unready': {'bg': 'var(--warning-bg, #ffeaa7)', 'fg': 'var(--warning-fg, #856404)', 'border': 'var(--warning-border, #ffeaa7)'},
                            'conditionally': {'bg': 'var(--error-bg, #f8d7da)', 'fg': 'var(--error-fg, #721c24)', 'border': 'var(--error-border, #f5c6cb)'},
                            'control_received': {'bg': '#e1e5ff', 'fg': '#4c63d2', 'border': '#b8c5ff'},
                            'in_progress': {'bg': '#d1ecf1', 'fg': '#0c5460', 'border': '#bee5eb'},
                            'completed': {'bg': 'var(--success-bg, #d4edda)', 'fg': 'var(--success-fg, #155724)', 'border': 'var(--success-border, #c3e6cb)'}
                        }
                        colors = status_colors.get(certificate.type, {'bg': '#f8f9fa', 'fg': '#333', 'border': '#ddd'})
                        html_parts.append(f"""
                            <div class="certificate-status" style="margin-left: 20px; 
                                       background: {colors['bg']}; 
                                       color: {colors['fg']};
                                       border: 1px solid {colors['border']};
                                       padding: 5px; 
                                       border-radius: 3px; 
                                       margin-top: 5px;">
                                <span class="emoji">🏆</span> Сертификат: <strong>{certificate.get_type_display()}</strong>
                            </div>
                        """)
                    
                    html_parts.append('</div>')
            else:
                html_parts.append('<div style="margin-left: 20px; color: var(--body-quiet-color, #666);">Нет оценок по данной сессии</div>')
            
            html_parts.append('</div>')
        
        if not html_parts:
            return "Нет записей о зачислении"
        
        return mark_safe(''.join(html_parts))
    get_detailed_progress.short_description = 'Детальный прогресс по сессиям'

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
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
    
    def get_students_count(self, obj):
        return obj.assessments.values('enrollment__student').distinct().count()
    get_students_count.short_description = 'Студентов'
    
    def get_avg_score(self, obj):
        final_assessments = obj.assessments.filter(is_final_grade=True)
        if final_assessments.exists():
            avg = sum(float(a.score) for a in final_assessments) / final_assessments.count()
            return f"{avg:.1f}"
        return "Нет оценок"
    get_avg_score.short_description = 'Средний балл'

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
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
    inlines = [AttendanceInline, AssessmentInline]
    list_per_page = 20
    
    def get_student_name(self, obj):
        return obj.student.full_name
    get_student_name.short_description = 'Студент'
    
    def get_session_number(self, obj):
        return f"Сессия №{obj.session.session_number}"
    get_session_number.short_description = 'Сессия'
    
    def get_attendance_status(self, obj):
        attendance = obj.attendances.first()
        if attendance:
            return "✅" if attendance.present else "❌"
        return "?"
    get_attendance_status.short_description = 'Присутствие'

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """ Класс для отображения в админке модели Attendance """
    list_display = (
        "get_student_name",
        "get_session_number",
        "present",
    )
    list_filter = ("present", "session")
    search_fields = ("enrollment__student__full_name",)
    
    def get_student_name(self, obj):
        return obj.enrollment.student.full_name
    get_student_name.short_description = 'Студент'
    
    def get_session_number(self, obj):
        return f"Сессия №{obj.session.session_number}"
    get_session_number.short_description = 'Сессия'

@admin.register(AssessmentType)
class AssessmentTypeAdmin(admin.ModelAdmin):
    """ Класс для отображения в админке модели AssessmentType """
    list_display = ("name", "weight", "get_assessments_count")
    ordering = ("name",)
    
    def get_assessments_count(self, obj):
        return obj.assessments.count()
    get_assessments_count.short_description = 'Количество оценок'

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    """ Модель для отображения в админке модели Assessment """
    list_display = (
        "get_student_name",
        "course",
        "type",
        "score",
        "date",
        "is_final_grade",
        "certificate_issued"
    )
    list_filter = ("course", "type", "date", "is_final_grade")
    search_fields = ("enrollment__student__full_name", "course__title")
    date_hierarchy = "date"
    list_per_page = 50
    
    def get_student_name(self, obj):
        return obj.enrollment.student.full_name
    get_student_name.short_description = 'Студент'

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """ Модель для отображения в админке модели Certificate """
    list_display = (
        "student",
        "course",
        "type",
        "issued_on",
        "has_assessment",
        "get_assessment_score"
    )
    list_filter = ("type", "course", "issued_on")
    search_fields = ("student__full_name", "course__title")
    date_hierarchy = "issued_on"
    list_per_page = 50
    
    def has_assessment(self, obj):
        return obj.assessment is not None
    has_assessment.boolean = True
    has_assessment.short_description = 'Есть оценка'
    
    def get_assessment_score(self, obj):
        if obj.assessment:
            grade_type = "Итоговая" if obj.assessment.is_final_grade else obj.assessment.type.name
            return f"{obj.assessment.score} ({grade_type})"
        return "Нет"
    get_assessment_score.short_description = 'Оценка'

@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    """ Модель для отображения в админке модели Statistic """
    list_display = (
        "student",
        "total_courses",
        "certified", 
        "uncertified",
        "sessions_attended",
        "sessions_missed",
        "sessions_late",
        "get_completion_percentage"
    )
    search_fields = ("student__full_name",)
    list_filter = ("sessions_attended", "sessions_missed")
    readonly_fields = ("student",)
    list_per_page = 50
    
    def get_completion_percentage(self, obj):
        if obj.total_courses > 0:
            percentage = (obj.certified / obj.total_courses) * 100
            return f"{percentage:.1f}%"
        return "0%"
    get_completion_percentage.short_description = 'Процент завершения'

