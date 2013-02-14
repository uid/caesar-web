from chunks.models import Assignment, Submission, File, Chunk, Batch, StaffMarker
from django.contrib.auth.models import User

import os
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
      staff_lines = open(file_path).read()
      staff_code[relative_path] = set([line.strip() for line in staff_lines.split('\n')])

  return staff_code

def get_type(file):
  if 'Test.java' in file.path:
    return 'test'
  return 'none'

def get_name(file):
  basename= os.path.basename(file.path)
  root,ext = os.path.splitext(basename)
  return root

def create_chunk(file):
  return Chunk(file=file, name=get_name(file), start=0, end=len(file.data), class_type=get_type(file), staff_portion=0, student_lines=0)

def create_file(file_path, submission, batch):
  file_data = open(file_path).read()
  return File(path=file_path, submission=submission, data=file_data, batch=batch)

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
  submission,created = Submission.objects.get_or_create(assignment=assignment, author=user, name=username)
  print submission
  if created:
    print "*** new submission for this student"

  file_objects = []
  chunk_objects = []

  # Creating the File objects
  for file_path in files:
    file = create_file(file_path, submission, batch)
    file_objects.append(file)
    if save:
      file.save()

    chunk = create_chunk(file)
    chunk_objects.append(chunk)
    if save:
      chunk.save()

    student_code = file.data.split('\n')
    num_student_lines = len(student_code)
    
    if staff_code:
      # Assuming that the student's directory looks like student_base_dir + '/' + username + '/' + project_name_dir
      num_subdirs = len(student_base_dir.split('/')) + 1 # + 1 for student username
      relative_path = '/'.join(file_path.split('/')[num_subdirs:])

      if relative_path in staff_code:
        # print "comparing with staff version of " + relative_path
        num_student_lines = 0
        staff_lines = []
        is_staff_line = False
        line_start = 0
        current_line = 0
        for line in student_code:
          if line.strip() in staff_code[relative_path]:
            if not is_staff_line:
              line_start = current_line
            is_staff_line = True
          else:
            num_student_lines += 1
            if is_staff_line:
              staff_lines.append((line_start, current_line - 1))
            is_staff_line = False
          current_line += 1

        if is_staff_line:
          staff_lines.append((line_start, current_line - 1))

        # print "staff lines = " + str(staff_lines)
        if save:
          for start, end in staff_lines:
            sm = StaffMarker(chunk=chunk, start_line=start+1, end_line=end+1)  # StaffMarker uses 1-based numbering
            sm.save()
      
    chunk.student_lines = num_student_lines
    if num_student_lines > 0:
      print str(chunk) + ": " + str(num_student_lines) + " new student lines"
    if save:
      chunk.save()
    
  return (submission, file_objects, chunk_objects)
