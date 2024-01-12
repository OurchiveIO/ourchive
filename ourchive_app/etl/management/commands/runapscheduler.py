# adapted from https://github.com/jcass77/django-apscheduler
import logging

from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util
from etl.ao3.work_import import EtlWorkImport
from etl.export.chive_export import ChiveExportOrchestrator

logger = logging.getLogger(__name__)


def process_works():
  importer = EtlWorkImport(0)
  importer.run_unprocessed_jobs()


def import_job_cleanup():
  importer = EtlWorkImport(0)
  importer.clean_old_jobs()


def process_exports():
  exporter = ChiveExportOrchestrator()
  exporter.run_unprocessed_jobs()


def export_job_cleanup():
  exporter = ChiveExportOrchestrator()
  exporter.clean_old_jobs()


# The `close_old_connections` decorator ensures that database connections, that have become
# unusable or are obsolete, are closed before and after your job has run. You should use it
# to wrap any jobs that you schedule that access the Django database in any way. 
@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
  """
  This job deletes APScheduler job execution entries older than `max_age` from the database.
  It helps to prevent the database from filling up with old historical records that are no
  longer useful.
  
  :param max_age: The maximum length of time to retain historical job execution records.
                  Defaults to 7 days.
  """
  DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
  help = "Runs APScheduler."

  def handle(self, *args, **options):
    scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
      process_works,
      trigger=CronTrigger(hour="*/2"),  # Every 2 hours
      id="process_works",  # The `id` assigned to each job MUST be unique
      max_instances=1,
      replace_existing=True,
    )
    logger.info("Added job 'process_works'.")

    scheduler.add_job(
      import_job_cleanup,
      trigger=CronTrigger(day="*/7"), 
      id="import_job_cleanup", 
      max_instances=1,
      replace_existing=True,
    )
    logger.info("Added job 'import_job_cleanup'.")

    scheduler.add_job(
      export_job_cleanup,
      trigger=CronTrigger(day="*/7"),
      id="export_job_cleanup", 
      max_instances=1,
      replace_existing=True,
    )
    logger.info("Added job 'export_job_cleanup'.")

    scheduler.add_job(
      process_exports,
      trigger=CronTrigger(minute="*/10"),
      id="process_exports", 
      max_instances=1,
      replace_existing=True,
    )
    logger.info("Added job 'process_exports'.")

    try:
      logger.info("Starting scheduler...")
      scheduler.start()
    except KeyboardInterrupt:
      logger.info("Stopping scheduler...")
      scheduler.shutdown()
      logger.info("Scheduler shut down successfully!")
