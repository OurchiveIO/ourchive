from django.db import connection, transaction
import logging

logger = logging.getLogger(__name__)
class ChiveFacetCleaner:
	def clean_up_facets(self):
		try:
			with connection.cursor() as cursor:
				cursor.execute("""UPDATE core_tagtype tt SET show_for_browse = false 
									WHERE NOT EXISTS (SELECT cwt.tag_id 
				  					FROM core_work_tags cwt 
				  					WHERE cwt.tag_id in (SELECT ct.id 
				  					FROM core_tag ct WHERE ct.tag_type_id = tt.id ))""")
				cursor.execute("""UPDATE core_attributetype cat SET show_for_browse = false 
									WHERE NOT EXISTS (SELECT cwa.attributevalue_id 
				  					FROM core_work_attributes cwa 
				  					WHERE cwa.attributevalue_id in (SELECT ca.id 
				  					FROM core_attributevalue ca WHERE ca.attribute_type_id = cat.id))""")
				transaction.commit()
		except Exception as err:
			logger.error(f'Export job cleanup failed: {err}')