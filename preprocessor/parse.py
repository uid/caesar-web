from chunks.models import Assignment, Submission, File, Chunk, Batch
from django.contrib.auth.models import User

failed_users = []

def get_type(file):
  if 'Test.java' in file.path:
    return 'test'
  return 'none'

def get_name(file):
  return file.path.split('.')[0]

def create_chunk(file):
  return Chunk(file=file, name=get_name(file), start=0, end=len(file.data), class_type=get_type(file), staff_portion=0, student_lines=0)

def create_file(file_path, submission):
  #file_data = open(file_path).read().decode()
  file_data = open(file_path).read()
  return File(path=file_path, submission=submission, data=file_data)

def parse_files(username, files, batch, assignment, save):
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

  return (submission, file_objects, chunk_objects)
