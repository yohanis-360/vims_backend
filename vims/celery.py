"""
Celery configuration for VIMS Backend.
Handles async tasks like photo processing, report generation, attention scores.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vims.settings')

app = Celery('vims')

# Load config from Django settings with 'CELERY' prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Periodic tasks schedule
app.conf.beat_schedule = {
    # Update attention scores every 5 minutes
    'calculate-attention-scores': {
        'task': 'apps.centers.tasks.calculate_all_attention_scores',
        'schedule': crontab(minute='*/5'),
    },
    # Sync machine data every 2 minutes
    'sync-machine-data': {
        'task': 'apps.inspections.tasks.sync_machine_data',
        'schedule': crontab(minute='*/2'),
    },
    # Check geofence violations every 10 minutes
    'check-geofence-violations': {
        'task': 'apps.inspections.tasks.check_geofence_violations',
        'schedule': crontab(minute='*/10'),
    },
    # Generate daily reports at midnight
    'generate-daily-reports': {
        'task': 'apps.reports.tasks.generate_daily_reports',
        'schedule': crontab(hour=0, minute=0),
    },
    # Clean old cache entries every hour
    'cleanup-cache': {
        'task': 'apps.core.tasks.cleanup_expired_cache',
        'schedule': crontab(minute=0),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')





