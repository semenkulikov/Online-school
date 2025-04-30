from django.db import models


class Session(models.Model):
    """ Модель для сессии """
    session_number = models.PositiveSmallIntegerField("Номер сессии")

class Student(models.Model):
    """ Модель для студента """
    full_name = models.CharField("ФИО", max_length=200)
    email = models.EmailField("E-mail", unique=True)
    start_date = models.DateField("Дата начала обучения")
    status = models.CharField('Статус', max_length=20, choices=[
        ('active','Активен'),('suspended','Приостановлен'),
    ], default='active')

    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
class Course(models.Model):
    """ Модель для предмета (курса) """
    title = models.CharField("Название предмета", max_length=200)
    description = models.TextField("Описание предмета", blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.title} (сессия {self.session.session_number})"
    
class Enrollment(models.Model):
    """ Запись о зачислении студента на курс/сессию """
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_on = models.DateField(auto_now_add=True)
    status = models.CharField(choices=[('planned','Зачисляется'),
                                       ('in_progress','Учится'),
                                       ('completed','Закончил')], 
                              default='planned')

class Attendance(models.Model):
    """ Посещаемость: присутствие/отсутствие студента на конкретной сессии. """
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    present = models.BooleanField()  # Был ли студент на данной сессии

class AssessmentType(models.Model):
    """ Тип зачета (Контрольная, чтение книг) """
    name = models.CharField(max_length=100)

class Assessment(models.Model):
    """ 
    Оценка по конкретному типу в рамках одной сессии: ссылка на Enrollment, 
    AssessmentType, балл/результат, дата, выдан ли сертификат. 
    """
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    type = models.ForeignKey(AssessmentType, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()
    certificate_issued = models.BooleanField(default=False)

class Certificate(models.Model):
    """ 
    Сведения о выдаче свидетельства: 
    на какую оценку/курс, дата выдачи, файл/номер. 
    """
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE)
    issued_on = models.DateField()
    file = models.FileField(upload_to='certificates/')

class Statistic(models.Model):
    """ 
    Итоговые расчёты по студенту: 
    числа прослушанных/освидетельствованных предметов, пропусков, опозданий и т.п. 
    """
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    total_courses = models.IntegerField()
    certified = models.IntegerField()
    uncertified = models.IntegerField()
    sessions_missed = models.IntegerField()
    sessions_late = models.IntegerField()
    

