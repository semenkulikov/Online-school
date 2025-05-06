from django.core.management.base import BaseCommand
import openpyxl

from core.models import Student

class Command(BaseCommand):
    help = "Импорт из Excel"

    def add_arguments(self, parser):
        parser.add_argument('filepath', type=str)

    def handle(self, *args, **options):
        wb = openpyxl.load_workbook(options['filepath'], data_only=True)
        ws = wb.active

        # 1) Разбор шапки: 
        #    строка 1 содержит веса (75%,15%,10%, …) 
        #    строка 2 — названия предметов и типов зачётов
        header_weights = [cell.value for cell in ws[1] if cell.value is not None]
        header_names   = [cell.value for cell in ws[2] if cell.value is not None]

        # Парсим всех учеников.
        for cell in ws["B"]:
            if cell.value:
                if cell.fill.bgColor.indexed == 64: 
                    # Если ячейки имеют синий цвет, сохраняем в БД
                    Student.objects.get_or_create(full_name=cell.value)
                else:
                    break

        # В цикле проходимся по данным предмета (присутствие, типы зачетов, результаты и свидетельства)
        # Если есть присутствие - началась новая сессия. 
        # Колонка свидетельства - конец данных предмета, значит пошел следующий

        is_new_session = False
        for cell in ws[3]:
            if cell.value and cell.value.lower() in "присутствие":
                # Начало новой сессии. Сохраняем номер сессии
                is_new_session = True
                session_number = int(ws[f"{cell.column_letter}{cell.row - 1}"].value[0])
                print(session_number)
            for line_num in range(cell.row + 1, Student.objects.count() + 1):
                # Проходимся по строкам с студентами и последовательно для каждого записываем результат. 
                line_value = ws[f"{cell.column_letter}{line_num}"].value

                if cell.value and cell.value.lower() in "присутствие":
                    # Записываем присутствие студента в данной сессии
            

        exit()
        # Построим структуру:
        # sessions = [
        #   {
        #     'col_presence': 2,
        #     'courses': [
        #         {
        #           'title': "Учение о Боге",
        #           'weight_map': {'Контрольная':0.75, 'Чтение книг':0.15, …},
        #           'cols': {'Контрольная':3, 'Чтение книг':4, …},
        #           'col_result': 6,
        #           'col_cert_status': 7,
        #         },
        #         …
        #     ]
        #   },
        #   …
        # ]
        sessions = []
        col = 1
        while col <= ws.max_column:
            # найдём начало блока сессии по ячейке header_names[col-1] == 'присутствие'
            if header_names[col-1] is None: continue
            print(header_names[col-1].lower())
            if header_names[col-1] and 'присутств' in header_names[col-1].lower():
                
                sess = {'col_presence': col, 'courses': []}
                col += 1
                # затем читаем подряд курсы, пока не встретим следующий "присутствие" или пустую
                while col <= ws.max_column and 'присутств' not in (header_names[col-1] or '').lower():
                    # new course
                    title = header_names[col-1]
                    course_block = {'title': title, 'weight_map': {}, 'cols': {}}
                    # собираем типы зачётов для этого курса
                    while col <= ws.max_column and header_names[col-1]:
                        name = header_names[col-1]
                        weight = header_weights[col-1] or 0
                        if name.lower() in ('результат', 'свидетельства'):
                            # результат и статус
                            if name.lower()=='результат':
                                course_block['col_result'] = col
                            else:
                                course_block['col_cert_status'] = col
                            col += 1
                            break
                        # обычный тип зачёта
                        course_block['weight_map'][name] = float(weight)/100.0
                        course_block['cols'][name] = col
                        col += 1
                    sess['courses'].append(course_block)
                sessions.append(sess)
            else:
                col += 1

        print(sessions)
        exit()
        # 2) Создаём/обновляем Session и Course в БД
        for i, sess_def in enumerate(sessions, start=1):
            sess_obj, _ = Session.objects.get_or_create(session_number=i)
            for cdef in sess_def['courses']:
                Course.objects.update_or_create(
                    title=cdef['title'], session=sess_obj,
                    defaults={'description': ''}
                )

        # 3) По строкам — студенты и их данные
        for row in ws.iter_rows(min_row=4, max_row=ws.max_row):
            idx, fio = row[0].value, row[1].value
            if not fio: 
                continue
            student, _ = Student.objects.get_or_create(full_name=fio)

            # для каждой сессии
            for s_idx, sess_def in enumerate(sessions, start=1):
                pres = row[sess_def['col_presence']-1].value
                ses_obj = Session.objects.get(session_number=s_idx)

                # для каждого курса в сессии
                for cdef in sess_def['courses']:
                    course = Course.objects.get(title=cdef['title'], session=ses_obj)
                    enroll, _ = Enrollment.objects.get_or_create(
                        student=student, course=course
                    )
                    # Attendance
                    Attendance.objects.update_or_create(
                        enrollment=enroll, session=ses_obj,
                        defaults={'present': bool(pres)}
                    )
                    # Assessments
                    total = 0
                    for atype, w in cdef['weight_map'].items():
                        col = cdef['cols'][atype]
                        score = row[col-1].value or 0
                        total += score * w
                        at_obj, _ = AssessmentType.objects.get_or_create(name=atype)
                        Assessment.objects.update_or_create(
                            enrollment=enroll, type=at_obj, date=None,
                            defaults={'score': score, 'certificate_issued': False}
                        )
                    # result
                    res_score = row[cdef['col_result']-1].value or total
                    # здесь вы можете хранить total или сохранять в Assessment с type="Итог"
                    # Certificate status
                    cert_val = row[cdef['col_cert_status']-1].value
                    # по цвету ячейки: row[cdef['col_cert_status']-1].fill.start_color.rgb 
                    cert, _ = Certificate.objects.update_or_create(
                        assessment=Assessment.objects.get(enrollment=enroll, type=at_obj),
                        defaults={'issued_on': None, 'file':''}
                    )
        self.stdout.write(self.style.SUCCESS("Импорт завершён."))