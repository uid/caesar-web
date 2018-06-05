from review.models import Submission, File, Chunk, Batch, Comment
from django.contrib.auth.models import User
from xml.dom.minidom import parseString
from subprocess import Popen, PIPE
from collections import defaultdict
import re

checkstyle_settings = {
    'settings': '/var/django/caesar/preprocessor/checks.xml',
    'jar': '/var/django/caesar/preprocessor/checkstyle-5.9-all.jar',
    }

# ignored_warnings maps a class type (from the Chunk model)
# to a set of checkstyle modules whose warnings should be discarded
# in classes of that type.  The modules should be described by full Java classname.
ignored_warnings = defaultdict(set, {
    'test': set([ 'com.puppycrawl.tools.checkstyle.checks.javadoc.JavadocMethodCheck', 
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
def generate_comments(chunk, checkstyle_user, batch, suppress_comment_regexes):
  xml = run_checkstyle(chunk.file.path)
  comment_nodes = find_comment_nodes(xml)
  ignored = 0
  comments = []
  for node in comment_nodes:
    message = node.getAttribute('message')
    line = node.getAttribute('line')
    checkstyleModule = node.getAttribute('source')
    if checkstyleModule in ignored_warnings[chunk.class_type] or matchesAny(suppress_comment_regexes, chunk.file.path + ':' + message):
      ignored += 1
    else:
      comments.append(Comment(
        type='S',
        text=message,
        chunk=chunk,
        batch=batch,
        author=checkstyle_user,
        start=line,
        end=line))
  print "checkstyle: on", chunk.name, 'I made', len(comments), 'comments and ignored', ignored, 'minor problems'
  return comments

def matchesAny(regexes, string):
  for regex in regexes:
    if re.search(regex, string):
      return True
  return False

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

def generate_checkstyle_comments(code_objects, save, batch, suppress_comment_regexes):
  
  checkstyle_user,created = User.objects.get_or_create(username='checkstyle')

  i = 0
  for (submission, files, chunks) in code_objects:
    i += 1
    print "%s: %s chunks for this submission." % (submission, len(chunks))
    for chunk in chunks:
      if chunk.student_lines == 0:
        continue  # don't run checkstyle on code that student hasn't touched
      comments = generate_comments(chunk, checkstyle_user, batch, suppress_comment_regexes)
      if save:
        [comment.save() for comment in comments]
