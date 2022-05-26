from pathlib import Path

def is_tif(file_name):
  return Path(file_name).suffix.capitalize() in ['.tif','.tiff']