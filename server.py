from flask import Flask, render_template, request, redirect, session, flash, jsonify
from datetime import datetime
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "ThisIsSecret"

myData = connectToMySQL('myDB')

emailRegEx = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')


@app.route("/")
def home():

    return render_template("simple_wall.html")


@app.route("/wall")
def wall():

    if "logged_in" in session:
        if session["logged_in"] != False:
            session["users"] = myData.query_db("SELECT first_name, id FROM users WHERE id != %s;" % session["logged_in"])

            query = "SELECT messages.id, messages.user_id, messages.message, messages.created_at, CONCAT(users.first_name, ' ', users.last_name) AS sender_name FROM messages JOIN users ON messages.sender_id = users.id WHERE user_id = %(id)s;"
            data = { "id" : session["logged_in"] }
            session["messages"] = myData.query_db(query, data)
            session["messages_count"] = len(session["messages"])

            for message in session["messages"]:
                time_since = int((datetime.now() - message["created_at"]).total_seconds())
                if time_since > 31557600:
                    if time_since // 31557600 >= 2:
                        message["time_since"] = str(time_since // 31557600) + " Years ago"
                    else:
                        message["time_since"] = "1 Year ago"
                elif time_since > 2628000:
                    if time_since // 2628000 >= 2:
                        message["time_since"] = str(time_since // 2628000) + " Months ago"
                    else:
                        message["time_since"] = "1 Month ago"
                elif time_since > 604800:
                    if time_since // 604800 >= 2:
                        message["time_since"] = str(time_since // 604800) + " Weeks ago"
                    else:
                        message["time_since"] = "1 Week ago"
                elif time_since > 86400:
                    if time_since // 86400 >= 2:
                        message["time_since"] = str(time_since // 86400) + " Days ago"
                    else:
                        message["time_since"] = "1 Day ago"
                elif time_since > 3600:
                    if time_since // 3600 >= 2:
                        message["time_since"] = str(time_since // 3600) + " Hours ago"
                    else:
                        message["time_since"] = "1 Hour ago"
                elif time_since > 60:
                    if time_since // 60 >= 2:
                        message["time_since"] = str(time_since // 60) + " Minutes ago"
                    else:
                        message["time_since"] = "1 Minute ago"
                else:
                    message["time_since"] = str(time_since // 1) + " Seconds ago"

            if session["user_level"] == 9:
                session["all_users"] = myData.query_db("SELECT * FROM users;")
                return render_template("simple_wall_admin.html")
            else:
                return render_template("simple_wall_page.html")

    flash("Please log in to view that page!", "login")
    return redirect("/")


@app.route("/reg", methods=["POST"])
def reg():

    if len(request.form["first_name"]) <= 1:
        flash("Plese enter a valid first name", "first")
    elif not request.form["first_name"].isalpha():
        flash("Names may only contain letters", "first")

    if len(request.form["last_name"]) <= 1:
        flash("Plese enter a valid last name", "last")
    elif not request.form["last_name"].isalpha():
        flash("Names may only contain letters", "last")

    if len(request.form["email"]) <= 1:
        flash("Please enter a valid Email Address", "email")
    elif not emailRegEx.match(request.form["email"]):
        flash("You must enter a valid Email Address", "email")

    for user in myData.query_db("SELECT users.email FROM users;"):
        if request.form["email"] == user["email"]:
            flash("That email address is already registered!", "email")

    if len(request.form["password"]) == 0:
        flash("Please enter a password", "password")
    elif len(request.form["password"]) <= 7:
        flash("Password must be at least 8 characters", "password")

    if len(request.form["confirm_password"]) == 0:
        flash("Please confirm your password", "confirm")
    elif request.form["confirm_password"] != request.form["password"]:
        flash("Your passwords must match", "password")
        flash("Your passwords must match", "confirm")

    if "_flashes" in session.keys():
        session["first_name"] = request.form["first_name"]
        session["last_name"] = request.form["last_name"]
        session["email"] = request.form["email"]

        return redirect("/") #failure
    else:
        flash("You are now registered!", "head")
        query = "INSERT INTO users (first_name, last_name, email, password, user_level, created_at, updated_at) VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password)s, 0, now(), now());"
        data = { 
            "first_name" : request.form["first_name"],
            "last_name" : request.form["last_name"],
            "email" : request.form["email"],
            "password" : bcrypt.generate_password_hash(request.form["password"]),
            }
        newClientId = myData.query_db(query, data)
        users = myData.query_db("SELECT created_at FROM users WHERE id = " + str(newClientId))
        session["logged_in"] = newClientId
        session["first_name"] = request.form["first_name"]
        session["user_level"] = 0
        session["secret_hash"] = bcrypt.generate_password_hash(str(users[0]["created_at"]) + 'melon')
        return redirect("/wall")


@app.route("/login", methods=["POST"])
def logIn():

    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = { "email" : request.form["email"] }
    users = myData.query_db(query, data)

    session["email2"] = request.form["email"]

    if not users:
        flash("Incorrect email or password", "login")
        return redirect("/")

    if bcrypt.check_password_hash(users[0]["password"], request.form["password"]):
        session["logged_in"] = users[0]["id"]
        session["first_name"] = users[0]["first_name"]
        session["user_level"] = users[0]["user_level"]
        session["secret_hash"] = bcrypt.generate_password_hash(str(users[0]["created_at"]) + "melon")
        return redirect("/wall")
    else:
        flash("Incorrect email or password", "login")
        return redirect("/")


@app.route("/logout", methods=["POST", "GET"])
def logOut():

    session.clear()

    return redirect("/")


@app.route("/message", methods=["POST"])
def message():

    if len(request.form["message"]) < 1:
        flash("You can't send a blank message :P", "empty_message")
    elif len(request.form["message"]) > 250:
        flash("Too long! Under 250 characters please!", "empty_message")

    if "_flashes" in session.keys():
        return redirect("/wall") #failure
    else:
        flash("Message Sent!", "head")
        query = "INSERT INTO messages (user_id, message, sender_id, created_at, updated_at) VALUES (%(user_id)s, %(message)s, %(sender_id)s, now(), now());"
        data = { 
            "user_id" : request.form["send_message_to"],
            "message" : request.form["message"],
            "sender_id" : session["logged_in"]
            }
        message_id = myData.query_db(query, data)
        return redirect("/wall")


@app.route("/delete/<message_id>")
def delete(message_id):

    created = myData.query_db("SELECT created_at FROM users WHERE id = " + str(session["logged_in"]))

    if not bcrypt.check_password_hash(session["secret_hash"], str(created[0]["created_at"]) + "melon"):
        session["danger_message_id"] = "Message ID " + message_id
        return redirect("/danger")

    allowed = False
    if "messages" in session.keys():
        for message in session["messages"]:
            if int(message_id) == message["id"]:
                allowed = True

    if allowed:
        flash("Message Deleted!", "head")
        myData.query_db("DELETE FROM messages WHERE id = %s;" % message_id)
        return redirect("/wall")
    else:
        session["danger_message_id"] = "Message ID " + message_id
        return redirect("/danger")


@app.route("/remove/<id>")
def remove(id):

    created = myData.query_db("SELECT created_at FROM users WHERE id = " + str(session["logged_in"]))

    if not bcrypt.check_password_hash(session["secret_hash"], str(created[0]["created_at"]) + "melon"):
        session["danger_message_id"] = "Access to ID " + id
        return redirect("/danger")

    if not "user_level" in session or session["user_level"] != 9:
        session["danger_message_id"] = "Access to ID " + id
        return redirect("/danger")
    else:
        myData.query_db("DELETE FROM users WHERE id = %(id)s;", {"id" : id})
        return redirect("/wall")



@app.route("/admin_access/<id>/<current_level>")
def admin_access(id, current_level):

    created = myData.query_db("SELECT created_at FROM users WHERE id = " + str(session["logged_in"]))

    if not bcrypt.check_password_hash(session["secret_hash"], str(created[0]["created_at"]) + "melon"):
        session["danger_message_id"] = "Access to ID " + id
        return redirect("/danger")

    if not "user_level" in session or session["user_level"] != 9:
        session["danger_message_id"] = "Access to ID " + id
        return redirect("/danger")
    else:
        if current_level == '9':
            myData.query_db("UPDATE users SET user_level = 0 WHERE id = %(id)s;", {"id" : id})
        else:
            myData.query_db("UPDATE users SET user_level = 9 WHERE id = %(id)s;", {"id" : id})
        return redirect("/wall")



@app.route("/danger")
def danger():

    danger_message_id = session["danger_message_id"]
    vistors_id = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    if "danger_count" in session:
        session["danger_count"] += 1
    else:
        session["danger_count"] = 1

    if session["danger_count"] >= 2:
        session.clear()

    return render_template("simple_wall_danger.html", vistors_id = vistors_id, danger_message_id = danger_message_id)


if __name__ == "__main__":
    app.run(debug=True)