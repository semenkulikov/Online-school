FROM python:3.13-slim
LABEL authors="Semen Saifutdinov"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt               # устанавливаем зависимости
COPY . /app
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "Online_school.wsgi:application", "--bind", "0.0.0.0:8000"]