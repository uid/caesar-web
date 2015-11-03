import os, fnmatch
from collections import defaultdict

def crawl_submissions(base_dir, includes, excludes):
  '''Crawls the students code and returns a dictionary mapping student usernames to
  absolute file paths of their code. NOTE: Does not guarantee that the users exist
  on the server.
  Params:
    base_dir: directory that contains all of the student sub-directories
    includes: list of filename patterns (using fnmatch syntax) that should be uploaded to Caesar.
               For example, '*.java' would match both Foo.java and src/foo/Bar.java.
    excludes: list of filename patterns that should be excluded from the upload
  Returns:
    Dictionary mapping user names (i.e. directories) to a list of pathnames, all of which start with base_dir.
  '''
  student_dirs = os.listdir(base_dir)
  student_code = defaultdict(list)

  def matchesAnyPattern(filename, patterns):
    return reduce(lambda p1,p2: p1 or p2, [fnmatch.fnmatch(filename, pattern) for pattern in patterns], False)

  for student_dir in student_dirs:
    filepath = base_dir + '/' + student_dir
    # Make sure we only take non-hidden directories
    if (not os.path.isdir(filepath)) or student_dir[0] == '.':
      continue
    for root, _, files in os.walk(filepath):
      student_code[student_dir].extend([root + '/' + file_path for file_path in files])
    # Only take files that are included but not excluded.
    student_code[student_dir] = [filename for filename in student_code[student_dir] 
                                          if matchesAnyPattern(filename, includes) 
                                             and not matchesAnyPattern(filename, excludes)]
  return student_code
