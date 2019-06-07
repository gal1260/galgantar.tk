import os
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']

def hash_password(password):
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(15))

def establish_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def confirm_data(name, surname, email, number):
    import re
    if not re.search(r"^[a-zA-Z\ ]+$", name):
        return "Name must only contain characters"
    elif not re.search(r"^[a-zA-Z\ ]+$", surname):
        return "Surname must only contain characters"
    elif not re.search(r"[^@]+@[^@]+\.[^@]+", email):
        return "Invalid email address"
    elif not re.search(r"^[0-9\ \+]+$", number):
        return "Invalid phone number"

    return False #No mistakes found

def user_is_new(email):
    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT ID FROM Users WHERE Email = %s;""", (email,))
    connection.commit()

    if cursor.fetchone() == None:
        return False #No mistakes found
    else:
        return "Account already exists"

def insert_new_user(name, surname, password, email, number):
    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute("""
                    INSERT INTO Users (Name, Surname, Password, Email, Tel, Role)
                    VALUES(%s, %s, %s, %s, %s, %s);
                    """, (name, surname, hash_password(password).decode(), email, number, "admin"))

    cursor.close()
    connection.commit()
    connection.close()

def check_login(email, password):
    import bcrypt
    connection = establish_connection()
    cursor = connection.cursor()
    cursor.execute("""SELECT Password FROM Users WHERE Email = %s ;""", (email,)) #(x,) forces python to make a touple
    connection.commit()

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

    cursor.execute("SELECT * FROM Users")
    response = cursor.fetchall()

    cursor.close()
    connection.commit()
    connection.close()

    return response

def manual_execute():
    code = open("query.sql", "r").read()
    connection = establish_connection()
    cursor = connection.cursor()

    cursor.execute(code)

    print(cursor.fetchall())

    cursor.close()
    connection.commit()
    connection.close()


if __name__ == "__main__":
    #list_database()
    manual_execute()
