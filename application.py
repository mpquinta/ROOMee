import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd


# PROFILE_PICS = os.path.join('static', 'profile_pics')

# Configure application
app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = PROFILE_PICS

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///roomee.db")

@app.route("/forum", methods=["GET", "POST"])
@login_required
def forum():
    """Allows users to post/interact on a public forum"""
    user_rows = db.execute("SELECT username FROM users2")
    users = []
    for row in user_rows:
        username = row["username"]
        table_name = "".join([username, "forumpost"])
        users.append({
            "table": table_name,
            "username": row["username"]
            })

    if request.method == "GET":
        forums = []
        for row in users:
            # Check if a table exists
            check = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name", table_name=row["table"])

            if len(check)==1:
                forum_rows = db.execute("SELECT subject, BODY, comments, sender, timestamp FROM :table_name", table_name=row["table"])
                for f in forum_rows:
                    forums.append({
                        "subject": f["subject"],
                        "body": f["BODY"],
                        "comments": f["comments"],
                        "timestamp": f["timestamp"],
                        "author": row["username"],
                        "table": row["table"],
                        "sender": f["sender"]
                        })

        return render_template("forum.html", users=users, forums=forums)

    else:
        table_name = request.form.get("table_name")
        comment = request.form.get("comment")

        if not comment:
            return apology("Type a comment!")
        user_rows = db.execute("SELECT username FROM users2 WHERE user_id=:user_id", user_id=session["user_id"])
        current_user = user_rows[0]["username"]

        db.execute("INSERT INTO :table_name (comments, sender) VALUES (:comment, :current_user)", table_name=table_name, comment=comment, current_user=current_user)

        flash("Sent!")

        return render_template("forum.html")


@app.route("/inbox", methods=["GET", "POST"])
@login_required
def inbox():
    """Check messages"""
    if request.method == "GET":
        rows = db.execute("SELECT username FROM users2 WHERE user_id=:user_id", user_id=session["user_id"])
        current_user = rows[0]["username"]
        inbox_name = "_".join([current_user, "inbox"])

        # If user has not received any messages
        check = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name", table_name=inbox_name)
        if len(check) == 0:
            return apology("You don't have any messages yet!")

        inbox_rows = db.execute("SELECT sender, msg, timestamp FROM :inbox_name ORDER BY timestamp DESC", inbox_name=inbox_name)

        msgs = []
        for row in inbox_rows:
            msgs.append({
                "sender": row["sender"],
                "msg": row["msg"],
                "timestamp": row["timestamp"]
            })

        return render_template("inbox.html", msgs=msgs)

    else:
        msg_orig = request.form.get("msg_orig")
        msg_reply = request.form.get("msg_reply")

        # Get current user's username
        rows = db.execute("SELECT username from users2 WHERE user_id=:user_id", user_id=session["user_id"])
        sender = rows[0]["username"]

        # Ensure a reply was typed in
        if not request.form.get("msg_reply"):
            return apology("You must type a response!")

        inbox_name = "_".join([msg_orig, "inbox"])
        check = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name", table_name=inbox_name)
        if len(check) == 1:
            db.execute("INSERT INTO :inbox_name (sender, recipient, msg) VALUES (:sender, :recipient, :msg)", inbox_name=inbox_name, sender=sender, recipient=msg_orig, msg=msg_reply)

        else:
            db.execute("CREATE TABLE :inbox_name (sender varchar(255), recipient varchar(255), msg varchar(2000), 'timestamp' timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP)", inbox_name=inbox_name)
            db.execute("INSERT INTO :inbox_name (sender, recipient, msg) VALUES (:sender, :recipient, :msg)", inbox_name=inbox_name, sender=sender, recipient=msg_orig, msg=msg_reply)

        flash("Message sent!")

        return render_template("inbox.html")



@app.route("/")
@login_required
def index():
    """Show user profile"""
    if request.method == "GET":
        # rows = db.execute("SELECT username FROM users2 WHERE id = :id", id=session["user_id"])
        # username = rows[0]["username"]

        # pp_rows = db.execute("SELECT username FROM users2 WHERE id != :id", id=session["user_id"])
        # mutuals = []
        # for row in pp_rows:
            # pp_file = "".join([row["username"], "profile_pic.jpg"])
            # profile_pic = url_for('static', filename='profile_pics/' + pp_file)
            # mutuals.append({
                # "Icon": profile_pic,
                # "Name": row["username"]
            # })

        profile_rows = db.execute("SELECT username, full_name, occupation, posting, room, rent, hobbies, profileImage FROM users2 WHERE user_id!=:user_id", user_id=session["user_id"])
        profile = []
        for row in profile_rows:
            profile.append({
                "Username": row["username"],
                "Name": row["full_name"],
                "Occupation": row["occupation"],
                "Posting": row["posting"],
                "Room": row["room"],
                "Rent": row["rent"],
                "Hobbies": row["hobbies"],
                "Icon": url_for('static', filename='profile_pics/' + row["profileImage"])
            })


        return render_template("index.html", profile=profile)

@app.route("/editprofile", methods=["GET", "POST"])
@login_required
def editprofile():
    """Allow user to edit profile"""
    if request.method == "GET":
        return render_template("editprofile.html")
    else:
        full_name = request.form.get("name")
        occupation = request.form.get("occupation")
        posting = request.form.get("posting")
        room = request.form.get("room")
        rent = request.form.get("rent")
        hobbies = request.form.get("hobbies")

        if not request.form.get("posting"):
            return apology("Please select what you are looking for.")
        if not request.form.get("room"):
            return apology("Please select desired living arrangement.")
        if not request.form.get("rent"):
            return apology("Please select a rent range.")

        # Check for current user's record
        rows = db.execute("SELECT user_id FROM users2 WHERE user_id=:user_id", user_id=session["user_id"])
        if len(rows) == 0:
            db.execute("INSERT INTO users2 (full_name, occupation, posting, room, rent, user_id, hobbies) VALUES (:full_name, :occupation, :posting, :room, :rent, :user_id, :hobbies)",
                    full_name=full_name, occupation=occupation, posting=posting, room=room, rent=rent, user_id=session["user_id"], hobbies=hobbies)

        db.execute("UPDATE users2 SET full_name=:full_name, occupation=:occupation, posting=:posting, room=:room, rent=:rent, hobbies=:hobbies WHERE user_id=:user_id", full_name=full_name, occupation=occupation, posting=posting, room=room,
                    rent=rent, user_id=session["user_id"], hobbies=hobbies)
        flash("Successfully updated!")
        return render_template("profile.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users2 WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/msg", methods=["GET", "POST"])
@login_required
def msg():
    """Lets users message another user"""
    if request.method == "GET":
        return render_template("msg.html")

    else:
        recipient = request.form.get("recipient")
        msg = request.form.get("msg")

        # Obtaining sender's username
        sender_rows = db.execute("SELECT username FROM users2 WHERE user_id=:user_id", user_id=session["user_id"])
        sender = sender_rows[0]["username"]

        # Ensure user types in a recipient's username
        if not request.form.get("recipient"):
            return apology("Enter someone's username!")
        # Ensure user types a message
        if not request.form.get("msg"):
            return apology("Don't be shy, say something!")
        # Ensure user is sending message to a valid user
        rows = db.execute("SELECT username FROM users2 WHERE username=:username", username=recipient)
        if len(rows) == 0:
            return apology("Please enter a valid username!")

        # Ensure user's inbox exists
        inbox_name = "_".join([recipient, "inbox"])
        check = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name", table_name=inbox_name)
        if len(check) == 1:
            db.execute("INSERT INTO :inbox_name (sender, recipient, msg) VALUES (:sender, :recipient, :msg)", inbox_name=inbox_name, sender=sender, recipient=recipient, msg=msg)

        else:
            db.execute("CREATE TABLE :inbox_name (sender varchar(255), recipient varchar(255), msg varchar(2000), 'timestamp' timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP)", inbox_name=inbox_name)
            db.execute("INSERT INTO :inbox_name (sender, recipient, msg) VALUES (:sender, :recipient, :msg)", inbox_name=inbox_name, sender=sender, recipient=recipient, msg=msg)

        flash("Message sent!")
        return redirect("/")

@app.route("/newpost", methods=["GET", "POST"])
@login_required
def newpost():
    if request.method == "GET":
        return render_template("newpost.html")

    else:
        subject = request.form.get("subject")
        body = request.form.get("body")

        # Ensure user has a subject line
        if not request.form.get("subject"):
            return apology("You must enter a subject line!")
        # Ensure user filled out body
        if not request.form.get("body"):
            return apology("You must fill out the body!")

        rows = db.execute("SELECT username FROM users2 WHERE user_id=:user_id", user_id=session["user_id"])
        username = rows[0]["username"]

        table_name = "".join([username, "forumpost"])
        db.execute("CREATE TABLE :table_name (subject varchar(255), body varchar(2000), comments varchar(2000), 'sender' text, 'timestamp' timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP)", table_name=table_name)
        db.execute("INSERT INTO :table_name (subject, body) VALUES (:subject, :body)", table_name=table_name, subject=subject, body=body)

        flash("Posted!")

        return render_template("forum.html")

@app.route("/profile", methods=["GET"])
@login_required
def profile():
    """User views their profile"""

    # If user reached the route via GET
    if request.method == "GET":
        rows = db.execute("SELECT full_name, occupation, posting, room, rent, hobbies FROM users2 WHERE user_id=:user_id", user_id=session["user_id"])
        profile = []
        for row in rows:
            profile.append({
                "Name": row["full_name"],
                "Occupation": row["occupation"],
                "Posting": row["posting"],
                "Room": row["room"],
                "Rent": row["rent"],
                "Hobbies": row["hobbies"]
            })

        pp_rows = db.execute("SELECT profileImage FROM users2 WHERE user_id=:user_id", user_id=session["user_id"])
        pp = pp_rows[0]["profileImage"]
        profile_pic = url_for('static', filename='profile_pics/' + pp)

        return render_template("profile.html", profile=profile, profile_pic=profile_pic)

    return apology("Sorry, something went wrong!")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # If user reached the route via GET
    if request.method == "GET":
        return render_template("register.html")

    # If user reached theh route via POST
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("password2")
        full_name = request.form.get("name")
        occupation = request.form.get("occupation")
        posting = request.form.get("posting")
        room = request.form.get("room")
        rent = request.form.get("rent")
        hobbies = request.form.get("hobbies")

        # Ensure that a username was entered
        if not request.form.get("username"):
            return apology("You must provide a username.")
        # Ensure that a password was entered
        if not request.form.get("password"):
            return apology("You must provide a password.")
        # Ensure that the password was typed again
        if not request.form.get("password2"):
            return apology("Please type your password again.")
        # Ensure that the password was type twice correctly
        if request.form.get("password") != request.form.get("password2"):
            return apology("The password you entered does not match. Please try again.")
        if not request.form.get("posting"):
            return apology("Please select what you are looking for.")
        if not request.form.get("room"):
            return apology("Please select desired living arrangement.")
        if not request.form.get("rent"):
            return apology("Please select a rent range.")

        # Ensure no one has the same username
        rows = db.execute("SELECT username FROM users2 WHERE username=:username", username=username)
        if len(rows) > 0:
            return apology("Sorry, that username's already taken.")

        # Add profileImage to files
        # Making a variable that holds pathway to "Images" folder
        target = os.path.join('static', 'profile_pics/')

        # If "images" folder doesn't exist, create one
        if not os.path.isdir(target):
            os.mkdir(target)

        # Store profileImage file upploaded by user in a variable
        file = request.files['profileImage']
        file.filename = "".join([username, "profile_pic", ".jpg"])

        # Create a variable where the pathway for the file will be stored
        destination = "/".join([target, file.filename])

        # Add login credentials to the database
        db.execute("INSERT INTO users2 (username, password, full_name, occupation, posting, room, rent, hobbies, profileImage) VALUES (:username, :password, :full_name, :occupation, :posting, :room, :rent, :hobbies, :profileImage)", username=username,
                    password = generate_password_hash(password), full_name=full_name, occupation=occupation, posting=posting, room=room, rent=rent, hobbies=hobbies, profileImage=file.filename)

        # Save the file into the destination
        file.save(destination)

        flash("Registered!")
        return redirect("/")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
