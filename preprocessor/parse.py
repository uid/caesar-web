from chunks.models import Assignment, Submission, File, Chunk, Batch, StaffMarker
from django.contrib.auth.models import User

from diff_match_patch import diff_match_patch, patch_obj
from crawler import crawl_submissions

# :( global variables
failed_users = []
diff_object = diff_match_patch()

def parse_staff_code(staff_dir):
  staff_files = crawl_submissions(staff_dir)
  num_subdirs = len(staff_dir.split('/'))
  staff_code = {}
  for files in staff_files.values():
    for file_path in files:
      relative_path = '/'.join(file_path.split('/')[num_subdirs:])
      staff_code[relative_path] = open(file_path).read()

  return staff_code

def get_type(file):
  if 'Test.java' in file.path:
    return 'test'
  return 'none'

def get_name(file):
  return file.path.split('.')[0]

def create_chunk(file):
  return Chunk(file=file, name=get_name(file), start=0, end=len(file.data), class_type=get_type(file), staff_portion=0, student_lines=0)

def create_file(file_path, submission):
  file_data = open(file_path).read()
  return File(path=file_path, submission=submission, data=file_data)

def parse_all_files(student_code, student_base_dir, batch, assignment, save, staff_code):
  return [parse_student_files(username, files, batch, assignment, save, student_base_dir, staff_code) for (username, files) in student_code.iteritems()]

def parse_student_files(username, files, batch, assignment, save, student_base_dir, staff_code):
  # staff_code is a dictionary from filename to staff code
  # Trying to find the user. Bail if they doen't exist in the DB.
  user = User.objects.filter(username=username)
  if (len(user) > 0):
    user = user[0]
  else:
    print "User %s doesn't exist in the database." % (username)
    failed_users.append(username)
    return None

  # Creating the Submission object
  submission = Submission(assignment=assignment, batch=batch, author=user, name=username)
  if save:
    submission.save()

  file_objects = []
  chunk_objects = []

  # Creating the File objects
  for file_path in files:
    file = create_file(file_path, submission)
    file_objects.append(file)
    if save:
      file.save()

    chunk = create_chunk(file)
    chunk_objects.append(chunk)
    if save:
      chunk.save()

    if staff_code:
      # Assuming that the student's directory looks like student_base_dir + '/' + username + '/' + project_name_dir
      num_subdirs = len(student_base_dir.split('/')) + 1 # + 1 for student username
      relative_path = '/'.join(file_path.split('/')[num_subdirs:])

      if relative_path in staff_code:
        diff = diff_object.diff_main(staff_code[relative_path], file.data)
        start_line = 0
        is_staff_code = False
        current_line = 0
        import pdb; pdb.set_trace()
        for diff_value, code in diff:
          if diff_value == -1:
            continue

          line_count = len(code.split('\n'))
          if code and code[-1] == '\n':
            line_count -= 1
          elif not code:
            line_count = 0
          if diff_value == 0 and not is_staff_code:
            is_staff_code = True
            start_line = current_line
          elif diff_value != 0:
            if is_staff_code:
              staff_marker = StaffMarker(chunk=chunk, start_line=start_line, end_line=current_line + line_count)
              if save:
                staff_marker.save()

              print staff_marker.start_line
              print staff_marker.end_line
              print ''

            is_staff_code = False

          current_line += line_count

        if is_staff_code:
          staff_marker = StaffMarker(chunk=chunk, start_line=start_line, end_line=current_line)
          if save:
            staff_marker.save()


        print ''
        print len(file.data.split('\n'))
        print '\n\n'

  return (submission, file_objects, chunk_objects)
