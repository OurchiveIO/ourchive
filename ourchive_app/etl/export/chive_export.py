import uuid
import logging
from etl.models import ChiveExport
from api import models as api
from django.utils.translation import gettext as _
from datetime import datetime, timedelta
import csv
from etl.export import export_helpers
import os
import shutil
from zipfile import ZipFile
import contextlib

logger = logging.getLogger(__name__)

class ChiveExportOrchestrator:
	def clean_old_jobs(self):
		try:
			import_jobs = ChiveExport.objects.filter(job_finished=True, created_on__lte=datetime.now()-timedelta(days=7)).filter(
			job_processing=False).delete()
		except Exception as err:
			logger.error(f'Export job cleanup failed: {err}')

	def run_unprocessed_jobs(self):
		export_jobs = ChiveExport.objects.filter(job_finished=False).filter(
			job_processing=False).order_by('created_on')[:100]
		zip_info = []
		for job in export_jobs:
			try:
				zip_info = self.export_chives(job)
				user = api.User.objects.get(id=job.user_id)
				user.chive_export_url = zip_info[1]
				user.save()
			except Exception as err:
				logger.error(
					f'Chive export: Exception executing export job {job.id}. Error: {err}')
				self.handle_job_fail(None, job)
				continue
		self.handle_batch_complete(export_jobs)

	def export_chives(self, job):
		# call file helper for filenames, pass filenames in to write_csv
		# create method to zip all files together/use file helper (check existing work export)
		filenames = []
		username = job.user.username
		loc_uuid = uuid.uuid4()
		if job.export_works:
			queryset = api.Work.objects.filter(user_id=job.user_id).filter(draft=False).all()
			file_info = ('works.csv', f'{export_helpers.get_temp_directory(username, loc_uuid)}works.csv')
			filenames.append(file_info)
			self.write_csv(queryset, file_info)
			for work in queryset:
				file_info = (
					f'work_chapters/{export_helpers.clean_text(work.title)}/chapters.csv',
					f'{export_helpers.get_temp_directory(username, loc_uuid)}/work/{export_helpers.clean_text(work.title)}/chapters.csv'
				)
				filenames.append(file_info)
				self.write_csv(work.chapters.filter(draft=False).all(), file_info)
		if job.export_bookmarks:
			queryset = api.Bookmark.objects.filter(user_id=job.user_id).filter(draft=False).all()
			file_info = ('bookmarks.csv', f'{export_helpers.get_temp_directory(username, loc_uuid)}bookmarks.csv')
			filenames.append(file_info)
			self.write_csv(queryset, file_info)
		if job.export_collections:
			queryset = api.BookmarkCollection.objects.filter(user_id=job.user_id).filter(draft=False).all()
			file_info = ('collections.csv', f'{export_helpers.get_temp_directory(username, loc_uuid)}collections.csv')
			filenames.append(file_info)
			self.write_csv(queryset, file_info)
		if job.export_series:
			queryset = api.WorkSeries.objects.filter(user_id=job.user_id).all()
			file_info = ('series.csv', f'{export_helpers.get_temp_directory(username, loc_uuid)}series.csv')
			filenames.append(file_info)
			self.write_csv(queryset, file_info)
		if job.export_anthologies:
			queryset = api.Anthology.objects.filter(creating_user_id=job.user_id).all()
			file_info = ('anthologies.csv', f'{export_helpers.get_temp_directory(username, loc_uuid)}anthologies.csv')
			filenames.append(file_info)
			self.write_csv(queryset, file_info)
		results = self.create_zip(filenames, username, loc_uuid)
		# clean up parent folder
		shutil.rmtree(export_helpers.get_temp_directory(username, loc_uuid))
		return results

	def write_csv(self, queryset, file_info):
		model = queryset.model
		model_fields = model._meta.fields + model._meta.many_to_many
		field_names = [field.name for field in model_fields]

		filename = file_info[1]
		dir_path = os.path.dirname(filename)
		os.makedirs(dir_path, exist_ok=True)

		# update csv writer to work with stream
		with open(filename, mode='w') as chive_file:
			writer = csv.writer(chive_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
			# Write a first row with header information
			writer.writerow(field_names)
			# Write data rows
			for row in queryset:
				values = []
				for field in field_names:
					value = getattr(row, field)
					if callable(value):
						try:
							items = []
							for item in value.all():
								friendly = item.display_text if hasattr(item, 'display_text') else f'{item}'
								items.append(friendly)
							value = items
						except Exception as ex:
							value = f'Error retrieving value: {ex}'
					if value is None:
						value = ''
					values.append(value)
				writer.writerow(values)

	def handle_job_fail(self, process_signal, job):
		logger.error(f'Chive export failed for {job.id}.')
		job.job_message = _(f'Export job for {job.user} failed. Check logs for errors.')
		job.job_success = False
		job.job_finished = True
		job.job_processing = False
		job.save()
		notif_string = _(f"Your export request has been processed. Your export(s) have failed. Please contact your admin for more information.")
		user = api.User.objects.filter(id=job.user_id).first()
		notification_type = api.NotificationType.objects.filter(
		type_label="System Notification").first()
		notification = api.Notification.objects.create(
			notification_type=notification_type,
			user=user,
			title=_("Chive Export Failed"),
			content=notif_string)
		notification.save()
		user.has_notifications = True
		user.save()
		return

	def handle_batch_complete(self, user_exports):
		for job in user_exports.all():
			job.job_message = _(f'Export job for {job.user} complete. Export works: {job.export_works} Export bookmarks: {job.export_bookmarks} Export collections: {job.export_collections}')
			job.job_success = True
			job.job_finished = True
			job.job_processing = False
			job.save()
			notif_string = _(f"Your export request has been processed. You can view your export files in your profile.")
			user = api.User.objects.filter(id=job.user_id).first()
			notification_type = api.NotificationType.objects.filter(
			type_label="System Notification").first()
			notification = api.Notification.objects.create(
				notification_type=notification_type,
				user=user,
				title=_("Chive Exports Processed"),
				content=notif_string)
			notification.save()
			user.has_notifications = True
			user.save()
		logger.info(f'Chive export batch processed.')

	def create_zip(self, files, username, loc_uuid):
		location = export_helpers.get_zip_dir(username, loc_uuid)
		zip_url = export_helpers.get_zip_url(username, loc_uuid)
		dir_path = os.path.dirname(location)
		os.makedirs(dir_path, exist_ok=True)
		with contextlib.suppress(FileNotFoundError):
			os.remove(location)
		with ZipFile(location, 'a') as chive_file:
			for file in files:
				# each file is a tuple: filename, full tmp path
				destination = file[0]
				source_path = file[1]
				chive_file.write(source_path, destination)
		return [location, zip_url]