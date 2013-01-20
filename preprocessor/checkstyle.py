from chunks.models import Assignment, Submission, File, Chunk, Batch
from review.models import Comment
from django.contrib.auth.models import User
from xml.dom.minidom import parseString
from subprocess import Popen, PIPE

checkstyle_settings = {
    'settings': '/home/mglidden/checkstyle-5.6/sun_checks.xml',
    'jar': '/home/mglidden/checkstyle-5.6/checkstyle-5.6-all.jar',
    }

def run_checkstyle(path):
  proc = Popen([
    'java',
    '-jar', checkstyle_settings['jar'],
    '-c', checkstyle_settings['settings'],
    '-f', 'xml',
    path],
    stdout=PIPE)
  return proc.communicate()[0]

# This probably won't support multi-chunks per file properly
def generate_comments(chunk, checkstyle_user, batch):
  xml = run_checkstyle(chunk.file.path)
  dom = parseString(xml)

  # Simple traversal of the DOM to find all errors.
  # Maybe easier to search for error tag, but this is easier ATM
  comments = []
  to_traverse = [dom]
  while to_traverse:
    node = to_traverse.pop()
    if node.nodeName == 'error' or node.nodeName == 'warning':
      comments.append(Comment(
        text=node.getAttribute('message'),
        chunk=chunk,
        batch=batch,
        author=checkstyle_user,
        start=node.getAttribute('line'),
        end=node.getAttribute('line')))
    else:
      to_traverse.extend(node.childNodes)
  print 'Found %s comments' % (len(comments))
  return comments

def generate_checkstyle_comments(code_objects, save, batch):
  checkstyle_user = User.objects.filter(username='checkstyle')
  if checkstyle_user:
    checkstyle_user = checkstyle_user[0]
  else:
    print "No checkstyle user. Can't upload comments."
    return

  i = 0
  for (submission, files, chunks) in code_objects:
    i += 1
    print "%s of %s. %s chunks for this submission." % (i, len(code_objects), len(chunks))
    for chunk in chunks:
      comments = generate_comments(chunk, checkstyle_user, batch)
      if save:
        [comment.save() for comment in comments]
