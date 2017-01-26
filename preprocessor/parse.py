from review.models import Submission, File, Chunk, StaffMarker
from django.contrib.auth.models import User

import os
from crawler import crawl_submissions

# :( global variables
failed_users = set()

def parse_staff_code(staff_dir, includes, excludes):
  staff_files = crawl_submissions(staff_dir, includes, excludes)
  num_subdirs = len(staff_dir.split('/'))
  staff_code = {}
  for files in staff_files.values():
    for file_path in files:
      relative_path = '/'.join(file_path.split('/')[num_subdirs+1:])
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

def create_file(file_path, submission):
  file_data = open(file_path).read()
  return File(path=file_path, submission=submission, data=file_data)

def split_into_usernames(folderName):
    return folderName.split("-")

def parse_all_files(student_code, student_base_dir, batch, submit_milestone, save, staff_code, restricted):
  code_objects = [
     parse_student_files(split_into_usernames(rootFolderName),
                         files,
                         batch,
                         submit_milestone,
                         save,
                         student_base_dir,
                         staff_code,
                         restricted)
    for (rootFolderName, files) in student_code.iteritems()]
  return [code_object for code_object in code_objects if code_object != None]

def parse_student_files(usernames, files, batch, submit_milestone, save, student_base_dir, staff_code, restricted):
  global failed_users

  # staff_code is a dictionary from filename to staff code
  # Trying to find the user(s) who wrote this submission. Bail if they don't all exist in the DB.
  users = User.objects.filter(username__in=usernames)
  
  if users.count() != len(set(usernames)):
    missing_users = set(usernames).difference([user.username for user in users])
    for username in missing_users:
      print "user %s doesn't exist in the database." % username
    failed_users |= missing_users
    return None

  submission_name = "-".join(usernames)
  
  # Shouldn't remake submissions
  if Submission.objects.filter(milestone=submit_milestone, authors__in=users).count() > 0:
    print "submission for %s already exists in the database." % submission_name
    return None

  # Creating the Submission object
  submission = Submission(milestone=submit_milestone, name=submission_name, batch=batch)
  if save:
    submission.save()
    for user in users:
      submission.authors.add(user)
    submission.save()

  print submission

  file_objects = []
  chunk_objects = []

  # Creating the File objects
  for file_path in files:
    file = create_file(file_path, submission)
    if len(file.data) == 0:
      continue # don't import empty files

    file_objects.append(file)
    if save:
      file.save()

    chunk = create_chunk(file)
    chunk_objects.append(chunk)
    if restricted: 
      chunk.chunk_info = 'restricted'
    if save:
      chunk.save()

    student_code = file.data.split('\n')
    num_student_lines = len(student_code)
    
    if staff_code:
      # Assuming that the student's directory looks like student_base_dir + '/' + username + '/' + project_name_dir
      num_subdirs = len(student_base_dir.split('/')) + 1 # + 1 for student username
      relative_path = '/'.join(file_path.split('/')[num_subdirs:])
      #print "looking for student path " + relative_path
      
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
