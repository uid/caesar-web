from chunks.models import Submission, File, Chunk, Batch
from review.models import Comment
from django.contrib.auth.models import User
from xml.dom.minidom import parseString
from subprocess import Popen, PIPE
from collections import defaultdict

checkstyle_settings = {
    'settings': '/var/django/caesar/preprocessor/checks.xml',
    'jar': '/var/django/caesar/preprocessor/checkstyle-5.7-all.jar',
    }

# ignored_warnings maps a class type (from the Chunk model)
# to a set of checkstyle modules whose warnings should be discarded
# in classes of that type.  The modules should be described by full Java classname.
ignored_warnings = defaultdict(set, {
    'TEST': set([ 'com.puppycrawl.tools.checkstyle.checks.javadoc.JavadocMethodCheck', 
                  'com.puppycrawl.tools.checkstyle.checks.coding.MagicNumberCheck' ])
})

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
  comment_nodes = find_comment_nodes(xml)
  ignored = 0
  for node in comment_nodes:
    if node.source in ignored_warnings[chunk.class_type]:
      ignored += 1
    else:
      comments.append(Comment(
        type='S',
        text=node.getAttribute('message'),
        chunk=chunk,
        batch=batch,
        author=checkstyle_user,
        start=node.getAttribute('line'),
        end=node.getAttribute('line')))
  print chunk.name, 'made', len(comments), 'and ignored', ignored
  return comments

def find_comment_nodes(xml):
  dom = parseString(xml)

  # Simple traversal of the DOM to find all errors.
  # Maybe easier to search for error tag, but this is easier ATM
  comment_nodes = []
  to_traverse = [dom]
  while to_traverse:
    node = to_traverse.pop()
    if node.nodeName == 'error' or node.nodeName == 'warning':
      comment_nodes.append(node)
    else:
      to_traverse.extend(node.childNodes)
  return comment_nodes

def generate_checkstyle_comments(code_objects, save, batch):
  checkstyle_user,created = User.objects.get_or_create(username='checkstyle')

  i = 0
  for (submission, files, chunks) in code_objects:
    i += 1
    print "%s of %s. %s chunks for this submission." % (i, len(code_objects), len(chunks))
    for chunk in chunks:
      if chunk.student_lines == 0:
        continue  # don't run checkstyle on code that student hasn't touched
      comments = generate_comments(chunk, checkstyle_user, batch)
      if save:
        [comment.save() for comment in comments]
