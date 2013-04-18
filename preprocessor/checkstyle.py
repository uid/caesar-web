import re

from chunks.models import Submission, File, Chunk, Batch
from review.models import Comment
from django.contrib.auth.models import User
from xml.dom.minidom import parseString
from subprocess import Popen, PIPE

checkstyle_settings = {
    'settings': '/var/django/caesar/preprocessor/checks.xml',
    'jar': '/var/django/caesar/preprocessor/checkstyle-5.6-all.jar',
    }

comment_regexs = {
    '.*is a magic number': 'important',
    'Missing a Javadoc comment': 'important',
    '.*must match pattern': 'important',
    'Inner assignments should be avoided': 'important',
    '.+ must match pattern': 'namingconvention',
    '.+ is a magic number': 'magicnumber',
    'Expected \\@param tag': 'javadoc',
    'Unused \\@throws tag': 'javadoc',
    'Unused \\@param tag': 'javadoc',
    'Expected \\@throws': 'javadoc',
    'Missing a Javadoc': 'javadoc',
    'Unused Javadoc tag.': 'javadoc',
    'Expected an \\@return tag': 'javadoc',
    'Unable to get class information for \\@throws tag': 'javadoc',
    'Duplicate \\@return tag': 'javadoc',
    '.+ construct must use .\\{\\}.s': 'braces',
    '.\\}. should be on the same line': 'braces',
    '.\\}. should be on a new line': 'braces',
    'Array brackets at illegal position.': 'braces',
    '.\\{. should be on the previous line.': 'braces',
    '.\\}. should be alone on a line': 'braces',
    'Method length is .+ max allowed is': 'size',
    'More than .+ parameters': 'size',
    'Inner assignments should be avoided': 'innerassignment',
    'Definition of .equals': 'hashcode',
    'Variable .+ must be private and have accessor methods': 'scope',
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

def _post_process_comment(comment):
  for regex, tag in comment_regexs.iteritems():
    if re.match(regex, comment):
      return "%s #%s" % (comment, tag)
  return comment

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
        text=_post_process_comment(node.getAttribute('message')),
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
