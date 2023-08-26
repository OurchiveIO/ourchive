from ourchiveao3importer.work_list import WorkList
from ourchiveao3importer.works import Work
from ourchiveao3importer.chapters import Chapters
import uuid
import logging
from etl.models import WorkImport, ObjectMapping
from api import models as api
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class EtlWorkImport(object):

    def __init__(self, user_id, save_as_draft=False, allow_anon_comments=False, allow_comments=True):
        self.save_as_draft = save_as_draft
        self.allow_anon_comments = allow_anon_comments
        self.allow_comments = allow_comments
        self.user_id = user_id
        self.error_message = ''
        self.success_message = _('Your work(s) have finished importing.')
        self.import_job = None

    def get_works_by_username(self, username):
        self.work_list = WorkList(username)
        self.work_list.find_work_ids()
        for work_id in self.work_list.work_ids:
            try:
                import_job = self.create_import_job(work_id)
            except Exception as err:
                logger.error(
                    f'Work import: Exception creating import job for: {work_id} username: {username}. Error: {err}')
                return False
        return True

    def run_unprocessed_jobs(self):
        import_jobs = WorkImport.objects.filter(job_finished=False).filter(
            job_processing=False).order_by('created_on')[:100]
        tracking_job = None
        user_imports = {}
        for job in import_jobs:
            self.import_job = job
            try:
                tracking_job = job
                self.user_id = job.user.id
                self.save_as_draft = job.save_as_draft
                self.allow_anon_comments = job.allow_anon_comments
                self.allow_comments = job.allow_comments
                processed = self.get_single_work(job.work_id, True, job)
                if processed:
                    if job.user.id in user_imports:
                        user_imports[job.user.id]['works'].append(f'{job.work_id}')
                        user_imports[job.user.id]['jobs'].append(job.id)
                    else:
                        user_imports[job.user.id] = {}
                        user_imports[job.user.id]['works'] = [f'{job.work_id}']
                        user_imports[job.user.id]['jobs'] = [job.id]
            except Exception as err:
                logger.error(
                    f'Work import: Exception executing import job {job.job_uid}. Error: {err}')
                self.handle_job_complete(None, tracking_job)
                continue
        self.handle_batch_complete(user_imports)

    def get_single_work(self, work_id, as_batch=False, import_job=None):
        if not as_batch:
            try:
                import_job = self.create_import_job(work_id)
            except Exception as err:
                logger.error(
                    f'Work import: Exception creating import job for {work_id}. Error: {err}')
            return None
        if import_job:
            chapters_processed = None
            try:
                chapters_processed = self.import_work(import_job.job_uid)
            except Exception as err:
                self.error_message = err
                logger.error(
                    f'Work import: Exception in get_single_work for {import_job.job_uid}. Error: {err}')
            if not as_batch or not chapters_processed:
                # if it's a single import or the import failed, let's go ahead and create a notif.
                # this prevents spamming on success of a username import
                self.handle_job_complete(chapters_processed, import_job)
            else:
                return 1

    def create_import_job(self, work_id):
        job_uid = uuid.uuid4()
        import_job = WorkImport(
            job_uid=job_uid,
            work_id=work_id,
            allow_comments=self.allow_comments,
            allow_anon_comments=self.allow_anon_comments,
            save_as_draft=self.save_as_draft,
            user_id=self.user_id
        )
        import_job.save()
        self.import_job = import_job
        return True

    def handle_job_complete(self, process_signal, import_job):
        if process_signal is None:
            self.handle_job_fail(import_job)
            logger.error(f'Work import failed for {import_job.job_uid}.')
            return
        self.handle_job_success(import_job)
        logger.info(f'Work import complete: {import_job.job_uid}.')

    def handle_batch_complete(self, user_imports):
        for user_id, process_info in user_imports.items():
            for job in process_info['jobs']:
                import_job = WorkImport.objects.get(pk=job)
                import_job.job_message = f'{self.success_message} {self.error_message}'
                import_job.job_success = True
                import_job.job_finished = True
                import_job.job_processing = False
                import_job.save()
            works_string = ", ".join(process_info['works'])
            notif_string = _(f"Your work import for work(s) {works_string} has been processed. You can view your works in your profile.")
            if self.error_message:
                notif_string = _(f'{notif_string} Some errors may have occurred: {self.error_message}. Contact your admin for more information.')
            user = api.User.objects.filter(id=user_id).first()
            notification_type = api.NotificationType.objects.filter(
                type_label="System Notification").first()
            notification = api.Notification.objects.create(
                notification_type=notification_type,
                user=user,
                title=_("Work Imports Processed"),
                content=notif_string)
            notification.save()
            user.has_notifications = True
            user.save()
        logger.info(f'Work import batch processed.')

    def import_work(self, job_uid):
        import_job = WorkImport.objects.filter(job_uid=job_uid).first()
        if not import_job:
            logger.error(
                f'Tried to import work for job that does not exist. Job uid: {job_uid}')
            return
        work_id = import_job.work_id
        if api.Work.objects.filter(user=import_job.user).filter(external_id=work_id).first() is not None:
            logger.info(
                f'Work {work_id} for user {import_job.user} already exists. Job {job_uid} is stale.')
            return 0
        # handle restricted & 404 errors here
        work_importer = None
        try:
            work_importer = Work(work_id)
        except Exception as err:
            self.error_message = err
            logger.error(
                f'Work import scraping for {work_id} in job {job_uid} failed: {err}')
            self.handle_job_fail(import_job)
            return
        work_dict = {}
        print(work_importer.json())
        try:
            work_dict = work_importer.__dict__()
        except Exception as err:
            self.error_message = err
            logger.error(f'Work dict for {work_id} in job {job_uid} failed: {err}')
            self.handle_job_fail(import_job)
            return
        work_processed_id = None
        try:
            work_processed_id = self.process_work_data(work_dict)
        except Exception as err:
            self.error_message = err
            logger.error(
                f'Process work data failed for {work_id} in job {job_uid}: {err}. Work dict: {work_dict}')
            self.handle_job_fail(import_job)
            return
        if work_processed_id is None:
            self.error_message = 'Could not retrieve work ID. Error may have occurred while processing data.'
            self.handle_job_fail(import_job)
            return
        try:
            chapters = Chapters(work_id)
        except Exception as err:
            self.error_message = err
            logger.error(f'Chapter import for {work_id} failed: {err}.')
            self.handle_job_fail(import_job)
            return
        try:
            chapters.chapter_contents()
        except Exception as err:
            self.error_message = err
            logger.error(f'Scraping chapter contents failed for {job_uid}: {err}.')
            self.handle_job_fail(import_job)
            return
        try:
            chapter_dict = chapters.__dict__() if chapters else {}
            chapters_processed = self.process_chapter_data(
                chapter_dict, work_processed_id)
            return chapters_processed
        except Exception as err:
            self.error_message = err
            logger.error(
                f'Process chapter data failed for {work_id} in job {job_uid}: {err}. Chapter dict: {chapter_dict}')
            self.handle_job_fail(import_job)
            return

    def process_mappings(self, obj, mappings, origin_json):
        for mapping in mappings:
            try:
                if "." in mapping.origin_field:
                    # we only need to support depth 2 here
                    mapping_split = mapping.origin_field.split(".")
                    origin_value = origin_json[mapping_split[0]][mapping_split[1]]
                else:
                    origin_value = origin_json[mapping.origin_field]
                if origin_value is None:
                    continue
                if 'tag' in mapping.destination_field:
                    try:
                        # create tag
                        tag_type_label = mapping.destination_field.split(".")[1]
                        tag_type = api.TagType.objects.filter(label=tag_type_label).first()
                        if not tag_type:
                            tag_type = api.TagType(label=tag_type_label)
                            tag_type.save()
                        if type(origin_value) is list:
                            for text in origin_value:
                                tag = api.Tag.find_existing_tag(text, tag_type.id)
                                if not tag:
                                    try:
                                        tag = api.Tag(text=text.lower(),
                                                  display_text=text, tag_type=tag_type)
                                        tag.save()
                                    except Exception as err:
                                        logger.error(f'Error creating tag with text {text.lower()} on obj {obj.id}: {err}')
                                        continue
                                obj.tags.add(tag)
                        else:
                            tag = api.Tag.find_existing_tag(origin_value, tag_type.id)
                            if not tag:
                                try:
                                    tag = api.Tag(text=origin_value.lower(),
                                              display_text=origin_value, tag_type=tag_type)
                                    tag.save()
                                except Exception as err:
                                    logger.error(f'Error creating tag with text {origin_value.lower()} on obj {obj.id}: {err}')
                                    continue
                            obj.tags.add(tag)
                    except Exception as err:
                        logger.error(f'Error processing tag with text {text.lower()} on obj {obj.id}: {err}')
                        continue
                elif 'attribute' in mapping.destination_field:
                    # create attribute
                    attribute_type_label = mapping.destination_field.split(".")[1]
                    attribute_type = api.AttributeType.objects.filter(
                        name=attribute_type_label.lower()).first()
                    if not attribute_type:
                        attribute_type = api.AttributeType(
                            name=attribute_type_label.lower(),
                            display_name=attribute_type_label,
                            allow_on_work=True,
                            allow_on_bookmark=True,
                            allow_on_chapter=True)
                        attribute_type.save()
                    if type(origin_value) is list:
                        for attribute_value in origin_value:
                            obj_attr = api.AttributeValue.objects.filter(
                                name=attribute_value.lower()).first()
                            if not obj_attr:
                                obj_attr = api.AttributeValue(
                                    name=attribute_value.lower(),
                                    display_name=attribute_value,
                                    attribute_type=attribute_type)
                                obj_attr.save()
                            obj.attributes.add(obj_attr)
                    else:
                        obj_attr = api.AttributeValue.objects.filter(
                            name=origin_value.lower()).first()
                        if not work_attr:
                            obj_attr = api.AttributeValue(
                                name=origin_value.lower(),
                                display_name=origin_value,
                                attribute_type=attribute_type)
                            obj_attr.save()
                        obj.attributes.add(obj_attr)
                else:
                    setattr(obj, mapping.destination_field, origin_value)
            except Exception as err:
                self.error_message = f'Error occurred processing mapping: {err}'
                logger.error(self.error_message)
                continue;
        obj.save()
        return obj.id

    def process_work_data(self, work_json):
        mappings = ObjectMapping.objects.filter(
            import_type='ao3', object_type='work').all()
        work_type_mapping = None
        work_type = None
        work_type_mapping = ObjectMapping.objects.filter(
            import_type='ao3', object_type='work_type')
        if not work_type_mapping:
            logger.error('Work type mapping not found. Trying to find Fic work type...')
            work_type_mapping = api.WorkType.objects.filter(type_name__iexact='Fic')
            if work_type_mapping is not None:
                work_type = work_type_mapping.first()
            else:
                work_type_mapping = api.WorkTypes.objects.all()
                if work_type_mapping is not None:
                    work_type = work_type_mapping.first()
                else:
                    logger.error('No work types found. Configure work types.')
                    return None
        else:
            type_name = work_type_mapping.first().destination_field
            try:
                work_type = api.WorkType.objects.filter(
                    type_name__iexact=type_name).first()
            except Exception as err:
                logger.error(
                    f'No work type found for mapping: {type_name} Error: {err}')
        work = api.Work(
            work_type=work_type,
            user_id=self.user_id,
            comments_permitted=self.allow_comments,
            anon_comments_permitted=self.allow_anon_comments,
            draft=self.save_as_draft,
            is_complete=True,
            external_id=self.import_job.work_id)
        work.save()
        work_id = self.process_mappings(work, mappings, work_json)
        if work_id:
            transl_note = _(f'Imported from Archive of Our Own. Original work id: {self.import_job.work_id}.')
            work.notes = f'{work.notes}<br/>{transl_note}'
        work.save()
        return work_id

    def process_chapter_data(self, chapter_json, work_id):
        mappings = ObjectMapping.objects.filter(
            import_type='ao3', object_type='chapter').all()
        chapter_ids = []
        chapter_num = 1
        for chapter_content in chapter_json['content']:
            chapter = api.Chapter(work_id=work_id, user_id=self.user_id,
                                  number=chapter_num, draft=False)
            chapter.save()
            chapter_ids.append(self.process_mappings(
                chapter, mappings, chapter_content))
            chapter_num += 1
        return chapter_ids

    def create_fail_notification(self, message=None):
        user = api.User.objects.filter(id=self.user_id).first()
        notification_type = api.NotificationType.objects.filter(
            type_label="System Notification").first()
        notification_message = _("Your work import was not successfully processed.")
        if message:
            notification_message = f"{notification_message} Error message: {message}. Contact your admin for more information."
        notification = api.Notification.objects.create(notification_type=notification_type, user=user, title=_("Work Import Processed"),
                                                       content=notification_message)
        notification.save()
        user.has_notifications = True
        user.save()

    def create_success_notification(self):
        user = api.User.objects.filter(id=self.user_id).first()
        notification_type = api.NotificationType.objects.filter(
            type_label="System Notification").first()
        notification = api.Notification.objects.create(notification_type=notification_type, user=user, title=_("Work Import Processed"),
                                                       content=_("Your work import has been processed. You can view your works in your profile."))
        notification.save()
        user.has_notifications = True
        user.save()

    def handle_job_fail(self, import_job):
        import_job = WorkImport.objects.get(pk=import_job.id)
        import_job.job_message = self.error_message
        import_job.job_success = False
        import_job.job_processing = False
        import_job.job_finished = True
        import_job.save()
        self.create_fail_notification()

    def handle_job_success(self, import_job):
        import_job = WorkImport.objects.get(pk=import_job.id)
        import_job.job_message = self.success_message
        import_job.job_success = True
        import_job.job_finished = True
        import_job.job_processing = False
        import_job.save()
        self.create_success_notification()
