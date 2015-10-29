import os, re
from collections import defaultdict

DEFAULT_FILE_EXTENSIONS = ['java', 'c', 'h', 'cpp', 'CC', 'py', 'scm', 'g4']
EXCLUDE_PATTERNS = ['ExpressionBaseListener', 'ExpressionLexer', 'ExpressionListener', 'ExpressionParser']

def file_extension(filename):
  if '.' in filename:
    return filename.split('.')[-1]
  return ''

def has_valid_file_extension_helper(file_extensions):
  def has_valid_file_extension(filename):
    return file_extension(filename) in file_extensions
  return has_valid_file_extension

def exclude_patterns_helper(patterns):
  def allow_filename(filename):
    for pattern in patterns:
      if re.search(pattern, filename):
        return False
    return True
  return allow_filename

def crawl_submissions(base_dir, file_extensions=DEFAULT_FILE_EXTENSIONS):
  '''Crawls the students code and returns a dictionary mapping student usernames to
  absolute file paths of their code. NOTE: Does not guarantee that the users exist
  on the server.
  Params:
    base_dir: directory that contains all of the student sub-directories
    file_extensions: which file extensions have source code in them. Default: ['java']
  Returns:
    Dictionary mapping user names (i.e. directories) to absolute path names of the code.
  '''
  student_dirs = os.listdir(base_dir)
  student_code = defaultdict(list)

  for student_dir in student_dirs:
    filepath = base_dir + '/' + student_dir
    # Make sure we only take non-hidden directories
    if (not os.path.isdir(filepath)) or student_dir[0] == '.':
      continue
    for root, _, files in os.walk(filepath):
      student_code[student_dir].extend([root + '/' + file_path for file_path in files])
    # Only take files of the extension we want.
    student_code[student_dir] = filter(has_valid_file_extension_helper(file_extensions), student_code[student_dir])
    # Remove excluded files
    student_code[student_dir] = filter(exclude_patterns_helper(EXCLUDE_PATTERNS), student_code[student_dir])

  return student_code


