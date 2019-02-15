from models import InstallationConfiguration
from peewee import DoesNotExist

def get_configuration(key, value_type):
  try:
    row = InstallationConfiguration.get(
            InstallationConfiguration.key == key)
  except DoesNotExist:
    return None
  return value_type(row.value)

def set_configuration(key, value):
  InstallationConfiguration.delete().where(
    InstallationConfiguration.key == key
  ).execute()
  config = InstallationConfiguration(
    key=key, value=value)
  config.save()

def get_bool_configuration(key):
  flag_value = get_configuration(key, int)
  # return 'true' value found -- i.e. if there is no value,
  # return None, not False
  return None if flag_value is None else bool(flag_value)

def set_bool_configuration(key, value):
  # store bool as int, as automatic string-casting will result
  # in 'True' and 'False' being stored, which both are bool() == True
  set_configuration(key, int(value))

# ---

# float values

def get_web_twitter_threshold():
  return get_configuration('THRESHOLD_WEB_TWITTER', float)

def set_web_twitter_threshold(value):
  set_configuration('THRESHOLD_WEB_TWITTER', value)

def get_print_threshold():
  return get_configuration('THRESHOLD_PRINT', float)

def set_print_threshold(value):
  set_configuration('THRESHOLD_PRINT', value)

def get_force_print_threshold():
  return get_configuration('THRESHOLD_FORCE_PRINT', float)

def set_force_print_threshold(value):
  set_configuration('THRESHOLD_FORCE_PRINT', value)

# int values

def get_web_twitter_every_once_in_n_matches():
  return get_configuration('ONCE_EVERY_N_WEB_TWITTER', int)

def set_web_twitter_every_once_in_n_matches(value):
  set_configuration('ONCE_EVERY_N_WEB_TWITTER', value)

def get_print_every_once_in_n_matches():
  return get_configuration('ONCE_EVERY_N_PRINT', int)

def set_print_every_once_in_n_matches(value):
  set_configuration('ONCE_EVERY_N_PRINT', value)

# bool flags

def get_force_print_flag():
  return get_bool_configuration('FLAG_FORCE_PRINT')

def set_force_print_flag(value):
  set_bool_configuration('FLAG_FORCE_PRINT', value)

def get_stop_printing_flag():
  return get_bool_configuration('FLAG_STOP_PRINTING')

def set_stop_printing_flag(value):
  set_bool_configuration('FLAG_STOP_PRINTING', value)
