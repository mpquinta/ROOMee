import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

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

@app.route("/")
@login_required
def index():
    """Show user profile"""
    if request.method == "GET":
        rows = db.execute("SELECT username FROM users WHERE id = :id", id=session["user_id"])
        username = rows[0]["username"]

        pf = db.execute("SELECT profileImage FROM users WHERE id=:id", id=session["user_id"])
        pp = rows[0]["profileImage"]

        return render_template("index.html", username=username, pp=pp)
    return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    return apology("TODO")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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


@app.route("/post", methods=["GET", "POST"])
@login_required
def quote():
    """User posts a new listing"""
    return apology("TODO")


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

        # Ensure no one has the same username
        rows = db.execute("SELECT username FROM users WHERE username = :username", username = username)
        if len(rows) > 0:
            return apology("Sorry, that username's already taken.")

        # Add profileImage to files
        # Making a variable that holds pathway to "Images" folder
        target = os.path.join(APP_ROOT, 'images/')

        # If "images" folder doesn't exist, create one
        if not os.path.isdir(target):
            os.mkdir(target)

        # Store profileImage file upploaded by user in a variable
        file = request.files['profileImage']

        # Create a variable where the pathway for the file will be stored
        destination = "/".join([target, file.filename])

        # Save the file into the destination
        file.save(destination)

        # Add login credentials to the database
        db.execute("INSERT INTO users (username, password, profileImage) VALUES (:username, :password, :profileImage)", username = username, password = generate_password_hash(password), profileImage=file.filename)

        return redirect("/")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
