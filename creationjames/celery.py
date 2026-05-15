from celery import Celery

app = Celery('creationjames')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
