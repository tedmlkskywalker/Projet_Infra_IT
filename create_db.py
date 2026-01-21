import sqlite3

connection = sqlite3.connect("database.db")

# Crée les tables définies dans schema.sql (bibliothèque)
with open("schema.sql") as f:
    connection.executescript(f.read())

cur = connection.cursor()

# ----------------------------
# USERS (gestion utilisateurs)
# ----------------------------
cur.execute("INSERT INTO users (username, role) VALUES (?, ?)", ("admin", "admin"))
cur.execute("INSERT INTO users (username, role) VALUES (?, ?)", ("user", "user"))

# ----------------------------
# BOOKS (livres + stock)
# ----------------------------
cur.execute("INSERT INTO books (title, author, stock) VALUES (?, ?, ?)", ("Harry Potter", "J.K. Rowling", 3))
cur.execute("INSERT INTO books (title, author, stock) VALUES (?, ?, ?)", ("Le Seigneur des Anneaux", "J.R.R. Tolkien", 2))
cur.execute("INSERT INTO books (title, author, stock) VALUES (?, ?, ?)", ("1984", "George Orwell", 1))
cur.execute("INSERT INTO books (title, author, stock) VALUES (?, ?, ?)", ("Dune", "Frank Herbert", 4))

connection.commit()
connection.close()
