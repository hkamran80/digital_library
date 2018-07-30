# Flask-powered {database} Catalog

from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import subprocess
import requests
import pymysql
import socket
import json
import time
import sys

app = Flask(__name__)
ip = socket.gethostbyname(socket.gethostname())

# Server functions
def metadata(isbn):
	"""Get book covers/data"""

	idb0 = BeautifulSoup(requests.get("https://www.amazon.com/s/ref=nb_sb_noss?field-keywords={}".format(isbn), headers={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:59.0) Gecko/20100101 Firefox/59.0"}).text, "html.parser")
	idb = BeautifulSoup(requests.get(idb0.find_all("ul", {"class":"s-result-list"})[0].find("li").find("a", {"class":"a-link-normal"})["href"], headers={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:59.0) Gecko/20100101 Firefox/59.0"}).text, "html.parser")
	
	try:
		title = idb.find("span", {"id":"productTitle"}).string
	except AttributeError:
		title = 0

	try:
		author = idb.find("a", {"class":"contributorNameID"}).string
	except AttributeError:
		author = "ERROR"

	return [title, author]

def add_book(isbn):
	title, author = metadata(isbn)

	try:
		conn = pymysql.connect("localhost", "{username}", "", "{database}")
		cursor = conn.cursor()
	except ConnectionRefusedError:
		if is_runnning("MAMP") == False:
			MAMP_up()

	cursor.execute("INSERT INTO books (title, author) VALUES ('{}', '{}')".format(title, author))
	conn.commit()

	cursor.close()

	return "Book successfully added!"

# Regular functions
cards = """
	<!DOCTYPE HTML>
	<html>
		<head>
			<title>Digital {database} Catalog for Python</title>
			<link rel="stylesheet" href="https://w3schools.com/w3css/4/w3.css">
			<link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">
			<link rel="stylesheet" href="static/css/{database}.css">

			<link rel="shortcut icon" href="static/favicon.ico">
			
			<script>
				// When the user scrolls down 20px from the top of the document, show the button
				window.onscroll = function() { scrollFunction() };

				function scrollFunction() {
				    if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
				        document.getElementById("goToTop").style.display = "block";
				    } else {
				        document.getElementById("goToTop").style.display = "none";
				    }
				}

				// When the user clicks on the button, scroll to the top of the document
				function goToTop() {
				    document.body.scrollTop = 0;
				    document.documentElement.scrollTop = 0;
				}
			</script>
		</head>
		<body>
			<button onclick="goToTop()" id="goToTop" title="Go to top"><i class="material-icons">arrow_upward</i></button>
			<header class="w3-container w3-teal" style="padding:16px;">
				<h3 style="font-family: 'Raleway', sans-serif;">Digital {database} Catalog for Python</h3>
			</header>
			<div id="books" style="margin-top:10px;text-align:center;">
	"""
book = """
	<div class="w3-card-4 w3-row">
		<div class="w3-col">
			<img src="static/covers/{}.jpg" width="260" height="341">
		</div>
		<div class="metadata">
			<span class="title" style="width:76px;">{}</span>
				<br>
			<span class="author">{}</span>
		</div>
	</div>
	"""
if sys.platform == "darwin":
	def is_runnning(app):
	    count = int(subprocess.check_output(["osascript",
	                "-e", "tell application \"System Events\"",
	                "-e", "count (every process whose name is \"" + app + "\")",
	                "-e", "end tell"]).strip())
	    return count > 0

	def MAMP_up():
		if is_runnning("MAMP") == False:
			output = [o.decode("utf-8") for o in subprocess.Popen(["open", "/Applications/MAMP/MAMP.app"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()]
			#print(output)
			time.sleep(7)

			return "MAMP online"
		else:
			return "MAMP already online"

def getBooks():
	return_data = []

	try:
		cursor = pymysql.connect("localhost", "{username}", "{password}", "{database}").cursor()
	except ConnectionRefusedError:
		if is_runnning("MAMP") == False:
			MAMP_up()

	try:
		cursor.execute("SELECT * FROM books")
		for row in cursor.fetchall():
			return_data.append([row[0], row[1], row[2]])

		books = []
		author_cleanup = lambda a: " ".join(a.split()[1:]) + " " + a.split()[0]

		for b in return_data:
			books.append([b[2].split()[-1] + " " + " ".join(b[2].split()[:-1]), b[1], b[0]])

		return_data = []
		books = sorted(books)

		for b in books:
			return_data.append([b[2], b[1], author_cleanup(b[0])])

		return return_data
	except:
		print("Error connecting to database. Checking if MAMP is started....")
		print("MAMP is running" if is_runnning("MAMP") else "MAMP is not running. Restarting MAMP...")
		if is_runnning("MAMP") == False:
			MAMP_up()

		#sys.exit("Error connecting to database.")

def populate(error=""):
	global cards, book

	print("Gathering books...")

	books = getBooks()

	if error != "":
		cards = cards + """
				<header class="w3-container w3-red" style="padding:5px;">{}</header>
		""".format(error)


	print("Parsing...")

	for b in books:
		cards = cards + book.format(b[0], b[1], b[2])

	#for d in r["books"]:
	#	cards = cards + book.format(d["id"], d["title"], d["author"])

	#books = books + "]"
	cards = cards + "</div></body>"

	return [cards, books]


print("="*60)

#populate()
print("Getting books and starting web server...")

@app.route("/", methods=["GET"])
def index():
	return populate()[0]
	#return cards

@app.route("/server", methods=["POST", "GET"])
def server():
	if request.method == "GET":
		return render_template("server.html")
	elif request.method == "POST":
		print(request.form["book_isbn"])
		print(metadata(request.form["book_isbn"]))

		return add_book(request.form["book_isbn"])

@app.route("/reload", methods=["POST"])
def reload():
	refresh()
	return "RELOADED LC"

@app.route("/search", methods=["POST"])
def search():
	global cards, book

	books = [b[1] for b in getBooks()]
	authors = [b[2] for b in getBooks()]
	query = request.form["query"]

	#print(books)
	
	try:
		bs = ""

		for b in books:
			if query in b:
				bs = bs + "::" + b + "__" + authors[books.index(b)]

		if bs == "":
			for b in books:
				if query.capitalize() in b:
					bs = bs + "::" + b + "__" + authors[books.index(b)]

		print(bs)

		if bs == "":
			return populate(error="No results found for query '{}'".format(query))[0]
		else:
			return bs
	except ValueError:
		return populate(error="No results found for query '{}'".format(query))[0]

	populate()

def refresh():
	global app

	print("="*30)

	# Check if MAMP (macOS MySQL/Apache (or Nginx) server) is running (that's where the DB is)
	print(MAMP_up())
	app.run(host="0.0.0.0", port=int(sys.argv[1]))
	time.sleep(86400)

try:
	refresh()
except ConnectionRefusedError:
	MAMP_up()
except pymysql.err.OperationalError:
	MAMP_up()
