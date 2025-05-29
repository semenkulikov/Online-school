from django.db import models
from django.utils.timezone import now


class Session(models.Model):
    """ Модель для сессии """

    class Meta:
        verbose_name = "Сессия"
        verbose_name_plural = "Сессии"
        ordering = ["session_number"]
    
    session_number = models.PositiveSmallIntegerField(verbose_name="Номер сессии")

    def __str__(self):
        return f"Сессия №{self.session_number}"

class Student(models.Model):
    """ Модель для студента """

    class Meta:
        verbose_name = "Студент"
        verbose_name_plural = "Студенты"
        ordering = ["full_name"]

    class Status(models.TextChoices):
        ACTIVE = "active", "Активен"
        SUSPENDED = "suspended", "Приостановлен"
    
    full_name = models.CharField("ФИО", max_length=200)
    email = models.EmailField("E-mail", unique=True, null=True)
    status = models.CharField("Статус", max_length=20, 
                              choices=Status.choices,
                              default=Status.ACTIVE)

    def __str__(self):
        if self.email:
            return f"{self.full_name} ({self.email})"
        return self.full_name
    
class Course(models.Model):
    """ Модель для предмета (курса) """

    class Meta:
        verbose_name = "Учебный предмет"
        verbose_name_plural = "Предметы"
        ordering = ["title"]
    
    title = models.CharField(max_length=200, verbose_name="Название предмета")
    description = models.TextField(blank=True, verbose_name="Описание предмета")
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="courses", verbose_name="Сессия")

    def __str__(self):
        return f"Курс: {self.title} (сессия {self.session.session_number})"
    
class Enrollment(models.Model):
    """ Запись о зачислении студента на сессию """

    class Meta:
        verbose_name = "Запись о зачислении студента на сессию"
        verbose_name_plural = "Записи о зачислении студента на сессию"
        ordering = ["-enrolled_on"]
        constraints = [
            models.UniqueConstraint(fields=["student", "session"], name="unique_enrollment")
        ]

    class Status(models.TextChoices):
        PLANNED = "planned", "Планируется"
        IN_PROGRESS = "in_progress", "Учится"
        COMPLETED = "completed", "Закончил"
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments", verbose_name="Студент")
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="enrollments", verbose_name="Сессия")
    enrolled_on = models.DateField(null=True, default=now, verbose_name="Дата зачисления")
    status = models.CharField(choices=Status.choices, 
                              default=Status.PLANNED,
                              max_length=20, verbose_name="Статус")

    def __str__(self):
        return f"Запись о зачислении для {self.student.full_name} (сессия {self.session.session_number})"

class Attendance(models.Model):
    """ Посещаемость: присутствие/отсутствие студента на конкретной сессии. """

    class Meta:
        verbose_name = "Посещаемость"
        verbose_name_plural = "Записи о посещаемости"

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="attendances")
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    present = models.BooleanField("Присутствовал")  # Был ли студент на данной сессии

    def __str__(self):
        return f"Посещаемость для {self.enrollment.student.full_name} (сессия №{self.session.session_number})"

class AssessmentType(models.Model):
    """ Тип зачета (Контрольная, чтение книг) """

    class Meta:
        verbose_name = "Тип зачета"
        verbose_name_plural = "Типы зачетов"
        ordering = ["name"]

    name = models.CharField(max_length=100, verbose_name="Название")
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Вес в итоговой оценке (%)")

    def __str__(self):
        return f"{self.name}"

class Assessment(models.Model):
    """ 
    Оценка по конкретному типу в рамках одной сессии: ссылка на Enrollment, 
    курс, тип зачета, балл/результат, дата, выдан ли сертификат. 
    """

    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"
        ordering = ["-date"]
    
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="assessments", verbose_name="Зачисление")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assessments", verbose_name="Предмет")
    type = models.ForeignKey(AssessmentType, on_delete=models.CASCADE, related_name="assessments", verbose_name="Тип зачета")
    score = models.DecimalField(max_digits=100, decimal_places=1, verbose_name="Балл")
    date = models.DateField(null=True, default=now, verbose_name="Дата")
    certificate_issued = models.BooleanField(default=False, verbose_name="Сертификат выдан")
    is_final_grade = models.BooleanField(default=False, verbose_name="Итоговая оценка за предмет")

    def __str__(self):
        grade_type = "Итоговая оценка" if self.is_final_grade else f"Оценка по {self.type.name}"
        return f"{grade_type} {self.score} для {self.enrollment.student.full_name} по {self.course.title}"

class Certificate(models.Model):
    """ 
    Сведения о выдаче свидетельства по предмету для студента
    """

    class Meta:
        verbose_name = "Сертификат"
        verbose_name_plural = "Сертификаты"
        ordering = ["-issued_on"]

    class Status(models.TextChoices):
        UNREADY = "unready", "Не выдан"
        CONDITIONALLY = "conditionally", "Условно-освидетельствовано (не все выполнено)"
        CONTROL_RECEIVED = "control_received", "Условно-освидетельствовано: поступила контрольная"
        IN_PROGRESS = "in_progress", "Готовится"
        COMPLETED = "completed", "Готов в электронной форме"
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="certificates")
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="certificates", null=True, blank=True)
    issued_on = models.DateField(null=True, default=now)
    file = models.FileField(upload_to='certificates/', blank=True, null=True)
    type = models.CharField("Статус", choices=Status.choices, 
                              default=Status.UNREADY,
                              max_length=20)

    def __str__(self):
        return f"Сертификат по {self.course.title} для {self.student.full_name}"

class Statistic(models.Model):
    """ 
    Итоговые расчёты по студенту: 
    числа прослушанных/освидетельствованных предметов, пропусков, опозданий и т.п. 
    """

    class Meta:
        verbose_name = "Статистика"
        verbose_name_plural = "Статистика"
    
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="statistic")
    total_courses = models.IntegerField("Кол. прослушанных предметов")
    certified = models.IntegerField("Кол. освидетельствованных предметов")
    uncertified = models.IntegerField("Кол. неосвидетельствованных предметов")
    sessions_missed = models.IntegerField("Кол. пропущенных сессий")
    sessions_attended = models.IntegerField("К-во сессий с момента начала обучения")
    sessions_late = models.IntegerField("К обуч. приступил с опозданием на (X) сессий", default=0)

    def __str__(self):
        return f"Статистика для {self.student.full_name}"
