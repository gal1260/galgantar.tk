import mail
import sys

def establish_connection():
    import os
    import psycopg2

    DATABASE_URL = os.environ['DATABASE_URL']

    return psycopg2.connect(DATABASE_URL, sslmode='require')

def hash_password(password):
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(15)).decode()

def confirm_data(name="a", surname="a", email="g@g.g", number="0"):
    import re

    if not re.search(r"^[a-zA-Z\ čšž]+$", name) and len(name) <= 100:
        return "Name must only contain characters"
    elif not re.search(r"^[a-zA-Z\ čšž]+$", surname) and len(surname) <= 100:
        return "Surname must only contain characters"
    elif not re.search(r"[^@]+@[^@]+\.[^@]+", email) and len(email) <= 30:
        return "Invalid email address"
    elif not re.search(r"^[0-9\ \+]+$", number) and len(number) <= 20:
        return "Invalid phone number"

    return False #No mistakes found

def user_is_new(email):
    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT ID FROM Users WHERE Email = %s;""", (email,))
    connection.commit()

    if cursor.rowcount == 0:
        return False #No mistakes found
    else:
        return "Account already exists"

def insert_new_user(name, surname, password, email, number):
    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute("""\
                    INSERT INTO Users (Name, Surname, Password, Email, Tel, Role)
                    VALUES(%s, %s, %s, %s, %s, %s);
                    """, (name, surname, hash_password(password), email, number, "user"))

    cursor.close()
    connection.commit()
    connection.close()

def check_login(email, password):
    import bcrypt
    connection = establish_connection()
    cursor = connection.cursor()
    cursor.execute("""SELECT Password FROM Users WHERE Email = %s ;""", (email,)) #(x,) forces python to make a touple

    response = cursor.fetchone()
    if not response:
        return False

    hash = response[0]
    connection.close()

    if password and bcrypt.checkpw(password.encode(), hash.encode()):
        return True
    else:
        return False

def list_database():
    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM Users ORDER BY Surname")
    response = cursor.fetchall()

    cursor.close()
    connection.commit()
    connection.close()

    return response

def get_user_data(email):
    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM Users WHERE Email = %s;", (email,))

    data = cursor.fetchone()
    cursor.close()
    connection.close()
    return data

def change_data(datatype_index, user_email, data):
    """Datatype index code: 0 = password, 1 = name, 2 = surname, 3 = telephone"""
    connection = establish_connection()
    cursor = connection.cursor()

    if datatype_index == 0:
        cursor.execute("UPDATE Users SET Password = %s WHERE Email = %s", (hash_password(data), user_email))
    elif datatype_index == 1:
        cursor.execute("UPDATE Users SET Name = %s WHERE Email = %s", (data, user_email))
    elif datatype_index == 2:
        cursor.execute("UPDATE Users SET Surname = %s WHERE Email = %s", (data, user_email))
    elif datatype_index == 3:
        cursor.execute("UPDATE Users SET Tel = %s WHERE Email = %s", (data, user_email))

    cursor.close()
    connection.commit()
    connection.close()

def get_current_date():
    """returns current date"""
    import datetime
    return datetime.datetime.utcnow().strftime('%Y-%m-%d')

def generate_confirmation_code():
    """generates random code and returns it with the time of creation"""
    from string import ascii_letters, digits
    from random import choice

    code = "".join([choice(ascii_letters+digits) for i in range(50)])
    confirmation_link = "http://galgantar.tk/confirmation/" + code

    return code

def email_conformation(email):
    """Sends email confirmation code"""
    code = generate_confirmation_code()
    confirmation_link = "http://galgantar.tk/confirmation/" + code
    time = get_current_date()

    connection = establish_connection()
    cursor = connection.cursor()
    cursor.execute("""\
                INSERT INTO Confirmations (Email, Code, Creation, Type)
                VALUES (%s, %s, %s, 'email')
                """, (email, code, time))
    cursor.close()

    mail.send_conformation(email, confirmation_link)

    connection.commit()
    connection.close()

def confirm_email(code):
    """Validates email confirmation code"""
    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT Email FROM Confirmations WHERE Code = %s", (code,))

    try:
        email = cursor.fetchone()[0]
        cursor.execute("UPDATE Users SET Confirmed = TRUE WHERE Email = %s", (email,))
        cursor.execute("DELETE FROM Confirmations WHERE Email = %s AND Type = 'email'", (email,))
        cursor.close()
        connection.commit()
        connection.close()
        return True

    except TypeError:
        pass

    cursor.close()
    connection.commit()
    connection.close()
    return False

def user_in_database(email):
    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT ID From Users WHERE Email = %s;", (email,))

    if cursor.rowcount != 0:
        connection.close()
        return True
    else:
        connection.close()
        return False

def reset_password(email):
    if not user_in_database(email):
        return False

    timed_code = generate_confirmation_code()
    confirmation_link = "http://galgantar.tk/password/" + timed_code[0] +"?email="+ email.replace("@", "<at>")
    time = timed_code[1]

    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute("""\
                    INSERT INTO Confirmations (Email, Code, Creation, Type)
                    VALUES (%s, %s, %s, 'password');
                    """, (email, timed_code[0], time))
    cursor.close()
    connection.commit()
    connection.close()

    mail.send_password_reset(email, confirmation_link)

def check_password_code(email, code):
    """Validates password reset code"""
    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT Email FROM Confirmations WHERE Email = %s AND Code = %s", (email, code))

    try:
        email = cursor.fetchone()[0]
        cursor.execute("DELETE FROM Confirmations WHERE Email = %s AND Type = 'password'", (email,))
        cursor.close()
        connection.commit()
        connection.close()
        return True

    except TypeError:
        pass

    cursor.close()
    connection.commit()
    connection.close()
    return False

def get_timetables():
    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute("""\
                    SELECT Tables.Name, Users.Name, Users.Surname
                    FROM Tables INNER JOIN Users
                    ON Tables.Creator = Users.Email
                    ORDER BY CreationDate DESC
                    """)

    data = cursor.fetchall()

    cursor.close()
    connection.close()

    return data

def new_timetable(name, days_binary, creator):
    connection = establish_connection()
    cursor = connection.cursor()

    creation_date = get_current_date()

    cursor.execute("""\
                    INSERT INTO Tables (Name, Creator, CreationDate, Days)
                    VALUES (%s, %s, %s, %s);
                    """, (name, creator, creation_date, "".join(days_binary)))
    cursor.close()
    connection.commit()
    connection.close()

def get_all_dates(day):
    """returns all dates for a specific day of the week from beginning to the end of the schoolyear"""
    from datetime import date, datetime, timedelta
    all_dates = []
    current_year = datetime.now().year

    if datetime.now().date() > date(current_year, 6, 19): # FIXME: Change to 24 later
        d = date(current_year, 9, 5) # Start
        end = date(current_year+1, 6, 15)
    else:
        d = date(current_year-1, 9, 5) # Start
        end = date(current_year, 6, 15)

    d += timedelta(day - d.weekday())

    while d < end:
        all_dates.append(d)
        d += timedelta(7)

    return all_dates

def get_timetable_dates(parent, email):
    import datetime
    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute("""\
                    SELECT Dates.MainDate, Users.Name, Users.Surname
                    FROM Dates INNER JOIN Users
                    ON Dates.Email = Users.Email
                    WHERE Dates.Parent = %s AND Dates.Active = TRUE
                    ORDER BY Dates.MainDate""", (parent,))

    formatted_dates = {}
    marked_dates = cursor.fetchall()

    for marked_date in marked_dates:
        date = marked_date[0].date()
        formatted_dates[date] =  marked_date[1]+" "+marked_date[2]

    cursor.execute("SELECT MainDate FROM Dates WHERE Parent = %s AND Email = %s AND Active = TRUE", (parent, email))

    if cursor.rowcount == 0:
        myDate = None
    else:
        myDate = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return formatted_dates, myDate

def get_timetable_properties(name):
    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT Days FROM Tables WHERE Name = %s", (name,))
    properties = cursor.fetchone()

    cursor.close()
    connection.close()

    return properties

def get_timetable_data(name, email):
    data = get_timetable_dates(name, email)
    taken_dates = data[0]
    if data[1]:
        myDate = data[1].strftime("%d.%m.%Y")
    else:
        myDate = None

    properties = get_timetable_properties(name)
    days = properties[0]
    final_dates = {}

    for n in range(5):
        if int(days[n]):
            dates = get_all_dates(n)

            for date in dates:
                final_dates[date] = []

    for date in final_dates:
        if date in taken_dates.keys():
            final_dates[date].append(taken_dates[date])

    sorted_dates = sorted(final_dates.items(), key=lambda x: x[0])

    slo_weekdays = ["Pon", "Tor", "Sre", "Čet", "Pet"]

    return map(lambda x: (slo_weekdays[x[0].weekday()], x[0].strftime("%d.%m.%Y"), x[1]), sorted_dates), myDate # Returns list (map) of tuples + myDate

def check_date_submission(email, parent):
    """Checks if submission for timetable already exists"""
    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT MainDate FROM Dates WHERE Email = %s and Parent = %s AND Active = TRUE", (email, parent))

    response = cursor.fetchone()

    if cursor.rowcount == 0:
        return False # No submissions found - OK
    else:
        return response[0].strftime("%d.%m.%Y")

def add_date(email, date, parent):
    check_submission = check_date_submission(email, parent)
    if check_submission:
        return "You have already submitted for a different date: {}".format(check_submission)

    connection = establish_connection()
    cursor = connection.cursor()

    date = date.split(".")
    date.reverse()
    date = "-".join(date)

    cursor.execute("""\
                    INSERT INTO Dates (Email, MainDate, Parent, Active)
                    VALUES (%s, %s, %s, TRUE);
                    """, (email, date, parent))

    cursor.close()
    connection.commit()
    connection.close()

    return False # No mistakes found

def remove_date(email, date, parent):
    connection = establish_connection()
    cursor = connection.cursor()

    date = date.split(".")
    date.reverse()
    date = "-".join(date)

    cursor.execute("""\
                    UPDATE Dates
                    SET Active = FALSE
                    WHERE Email = %s AND MainDate = %s AND Parent = %s
                    """, (email, date, parent))

    cursor.close()
    connection.commit()
    connection.close()

def manual_execute(code=None):
    if not code:
        code = open("query.sql", "r").read()

    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute(code)

    if cursor.statusmessage.split()[0] == "SELECT":
        response = cursor.fetchall()
        print(response, file=sys.stderr)

    cursor.close()
    connection.commit()
    connection.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "-user":
            print("Listing database...", end="\n\n", file=sys.stderr)
            manual_execute("SELECT * FROM Users")

        elif sys.argv[1] == "-confirm":
            print("Listing database...", end="\n\n", file=sys.stderr)
            manual_execute("SELECT * FROM Confirmations")

        elif sys.argv[1] == "-dates":
            print("Listing database...", end="\n\n", file=sys.stderr)
            manual_execute("SELECT * FROM Dates")

        elif sys.argv[1] == "-tables":
            print("Listing database...", end="\n\n", file=sys.stderr)
            manual_execute("SELECT * FROM Tables")
    else:
        manual_execute()
