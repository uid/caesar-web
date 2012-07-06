New Semester
============

1. Close all open reviewing assignments.  Go to 'http://caesar.csail.mit.edu/review/manage' and click 'close all assignments'. This remove any unfinished tasks from 'code to review' section on the dashboard. 

2. Update the user roster.  There is a helpful script 'loadusers.py' located in /var/django/caesar/scripts to do most of this, 
though you may need to do manual fixups by going to Admin / Users in the Caesar web interface.  Specifically, you need to:

  (a) Change students who passed the class to alums, and students who dropped or failed to inactive (they will no longer be able to log on, but their content will remain). Add/change staff. 

  (b) When you have the full roster of students for the new semester, load them into the system. 

3. In chunks.models change any references to 'current semester' to be the new semester.

New Assignment
============

### Create Assignment in Caesar
Go to: 
http://caesar.csail.mit.edu/admin/chunks/assignment/add/


The only fields you need to enter are these:

* [Name:] this is what all users of the system will see in reference to the assignment
* [Duedate:] Students will see when the problem set is due, if they are allowed extensions, extensions will count from the duedate. WARNING: Duedate is tricky to change later, if possible set it correctly the first time.
* [Code review end date:] *Set this field in the past while you're loading an assignment, so that visitors won't get code assigned to them until you're ready.*  This field controls if reviewing is allowed to be happening to this problem set. If current time < code review end date, the system will start assigning code if there is code loaded into the system. When creating the assignment set this date to before the duedate and when you want reviewing to open change this to something sensible. 
* [max extensions] and [multiplier] are only relevant if a slack day policy is used. See section Extensions. Set max extensions to 0 if slack days are not allowed for that problem set.

Ignore the rest of the fields.  There is a routing interface that will set these numbers, so anything you enter in them now will be overwritten anyway.



### Extensions
Students start out with 5 slack days of extension by default. This number is hardcoded into developer code.

This system was configured for two extension systems. For Fall 2011, the extension policy was max of 3 days per assignment (this number can be specified with 'max_extenion'). multiplier field should be set to 1. (1 day of pset extension means 1 less slack day for student)

For Spring 2012, there was the concept of beta and final, beta could be extended max of 12 hours but it would count as a full slack day being used for the students. For this max extension is set to 1 and multiplier is set to 2. 

To see who has asked for extensions, there is a handy scripts in /var/django/caesar/scripts, latesubmissions.py to get files of list of students that asked for extensions. Whoever is running the grading script will need this information.

Students may not request extensions if it is past the duedate of the problem set (or their extended duedate) + 30 minutes of grace period. 

### Load code

This will involve the preprocessor, which you'll need to check out from GitHub (https://github.com/uid/caesar-preprocessor) and compile with Eclipse.

The GitHub checkout is missing a Java class, Database, which contains configuration settings.  You'll need to obtain this from a previous TA.

Check to see that you are loading to the right database (Production vs Developer). 

Update to the relevant code in svn, or whatever code you want to load. 

Edit edu.mit.csail.caesar.Main to configure the load. Set the crawler path to the root directory of your student code tree:

    Crawler crawler = new BasicInvertedFileSystemCrawler("/Users/elena/Documents/sp12/sp12/users");

The preprocessor assumes that this path contains username folders (e.g. "bitdiddle"), and each username folder contains 
assignment folders (e.g. "ps4").

Set 'Assignment' to the assignment you're trying to load  

    Assignment assignment = new Assignment("ps4", "ps4-beta"); 

The first name is the folder name found in the student code tree, the second is the name that you gave to the assignment in Caesar. 

Similarly we need to point the preprocessor to the staff starter code. 

    Crawler staffCrawler = new BasicInvertedFileSystemCrawler("/Users/elena/Documents/6.005/chunks_staff");
    Assignment staffAssignment = new Assignment("ps4-starting", "ps4-final"); 

First name is what is in the directory, second name is irrelevant. 

Click Run. 

Note: Students in Caesar that also have the assignment folder in the path you specified, will get their code loaded. Everyone else's code will simply not get loaded. If some students are missing a problem set directory it is not a problem, their submission will be blank.

### Configure chunk routing
Once the preprocessor finishes, go to http://caesar.csail.mit.edu/review/studentstats. Check to see that the total number of chunks is what you would expect and the number of Checkstyle comments > 0. 
click - 'configure routing' to configure how chunks should be allocated to reviewers. Hopefully this part of the interface is self explanatory. 

### Open reviewing
Go back to the admin page for the assignment, http://caesar.csail.mit.edu/admin/chunks/assignment, pick your assignment and change the [Code review end date:] to something in the future. This will make the system start assignment users with chunks to review when they go to the dashboard.

### Update the dashboard's message of the day.

Every user's Caesar dashboard displays a message of the day, which briefly describes the assignment being reviewed
and provides a link to its handout. You need to edit this directly in the Caesar source code, in the file 
/var/django/caesar/templates/review/dashboard_toolbar.html. 

### Notify users
Send an email to relevant users that reviewing has opened.  At the moment, the best way to do this is to run /var/django/scripts/loadusers.py.  You may have to edit this script to produce the list of emails that you want.

### Helpful hints
If a user is complaining something is broken on their dashboard, you can go to http://caesar.csail.mit.edu/review/dashboard/_username_ to see what they see. 


Backups
===================
After every problem set, make a backup of the Caesar database as follows:

1. Go to phpMyAdmin (http://mysql.csail.mit.edu/phpmyadmin)

2. Log in as caesar_stage with the Caesar database password (see /var/django/caesar/settings_local.py for the passwd)

3. Choose the caesar_production database.

4. Go to Export, make sure Select All, SQL, and Save as File with template __DB__-%y-%m-%d, and gzipped.

5. Push Go.  Put the resulting file in /afs/csail/proj/courses/6.005/caesar_backups/.


