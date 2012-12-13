import settings
from re import match

def get_names():
    f = open(settings.project_path('accounts') + '/second-wave-alums.txt')
    user_parts = []
    for line in f:
        user_line = line.split()
        for part in user_line:
            comma = part.find(',')
            if comma != -1:
                user_parts.append(part[0:comma].lower())
            else:
                user_parts.append(part.lower())

    return user_parts

def check_name(first, last, email, username):
    user_parts = get_names()
    if email.lower() in user_parts:
        return True
    if first.lower() in user_parts or last.lower() in user_parts or username.lower() in user_parts:
        return True
    return False

def check_email(email):
    if len(email) > 13:
        if match("^[a-zA-Z0-9._%-+]+@alum\.mit\.edu$", email) != None:
            return True
    return False