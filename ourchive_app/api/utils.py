def convert_boolean(string_bool):
	if string_bool.lower() in ['true', 'yes', 'y', '1']:
		return True
	elif string_bool.lower() in ['false', 'no', 'n', '0']:
		return False
	else:
		raise ValueError("Value is not a boolean.")