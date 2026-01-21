from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask import Response
from functools import wraps
import sqlite3
import os

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# ✅ IMPORTANT : chemin absolu vers database.db (évite les bugs Alwaysdata)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


# ----------------------------
# Authentification ADMIN (session)
# ----------------------------
def est_authentifie():
    return session.get('authentifie')


# ----------------------------
# Authentification USER (Basic Auth) - user/12345
# ----------------------------
def require_user_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == "user" and auth.password == "12345"):
            return Response(
                "Accès refusé (user requis)",
                401,
                {"WWW-Authenticate": 'Basic realm="User Area"'}
            )
        return f(*args, **kwargs)
    return decorated


# ----------------------------
# Routes existantes (base)
# ----------------------------
@app.route('/')
def hello_world():
    return render_template('hello.html')


@app.route('/lecture')
def lecture():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    return "<h2>Bravo, vous êtes authentifié</h2>"


@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'password':
            session['authentifie'] = True
            return redirect(url_for('lecture'))
        else:
            return render_template('formulaire_authentification.html', error=True)

    return render_template('formulaire_authentification.html', error=False)


# ---------------------------------------------------
# Séquence 6 - Bibliothèque (HTML + routes API)
# ---------------------------------------------------

# ✅ Page admin HTML (ajout/suppression)
@app.route('/admin/books', methods=['GET'])
def admin_books():
    if not est_authentifie():
        return redirect(url_for('authentification'))
    return render_template('books_admin.html')


# ✅ Liste HTML des livres
@app.route('/books', methods=['GET'])
def books():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, author, stock FROM books')
    books = cursor.fetchall()
    conn.close()
    return render_template('books_list.html', books=books)


# ✅ Livres disponibles (JSON)
@app.route('/books/available', methods=['GET'])
def books_available():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, author, stock FROM books WHERE stock > 0')
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)


# ✅ Ajouter un livre (ADMIN) — utilisé par books_admin.html
@app.route('/books/add', methods=['POST'])
def add_book():
    if not est_authentifie():
        return redirect(url_for('authentification'))

    title = request.form.get('title')
    author = request.form.get('author')
    stock = request.form.get('stock', 1)

    if not title or not author:
        return "Champs manquants: title et author", 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO books (title, author, stock) VALUES (?, ?, ?)',
        (title, author, int(stock))
    )
    conn.commit()
    conn.close()

    return redirect('/admin/books')


# ✅ Supprimer un livre (ADMIN) — utilisé par books_admin.html
@app.route('/books/delete', methods=['POST'])
def delete_book():
    if not est_authentifie():
        return redirect(url_for('authentification'))

    book_id = request.form.get('book_id')
    if not book_id:
        return "book_id manquant", 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
    conn.commit()
    conn.close()

    return redirect('/admin/books')


# ✅ Emprunter un livre (USER) — API POST
@app.route('/loan/<int:book_id>', methods=['POST'])
@require_user_auth
def loan_book(book_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT stock FROM books WHERE id = ?', (book_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Livre introuvable", 404

    stock = row[0]
    if stock <= 0:
        conn.close()
        return "Livre indisponible", 400

    cursor.execute('UPDATE books SET stock = stock - 1 WHERE id = ?', (book_id,))
    cursor.execute('INSERT INTO loans (user_id, book_id) VALUES (?, ?)', (1, book_id))

    conn.commit()
    conn.close()
    return "Livre emprunté"


# ✅ Retourner un livre (USER) — API POST
@app.route('/return/<int:book_id>', methods=['POST'])
@require_user_auth
def return_book(book_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        'UPDATE loans SET return_date = CURRENT_TIMESTAMP '
        'WHERE book_id = ? AND return_date IS NULL',
        (book_id,)
    )
    cursor.execute('UPDATE books SET stock = stock + 1 WHERE id = ?', (book_id,))

    conn.commit()
    conn.close()
    return "Livre retourné"


# ✅ Routes de test GET (pour cliquer depuis books_list.html)
@app.route('/loan_test/<int:book_id>', methods=['GET'])
@require_user_auth
def loan_test(book_id):
    return loan_book(book_id)


@app.route('/return_test/<int:book_id>', methods=['GET'])
@require_user_auth
def return_test(book_id):
    return return_book(book_id)


if __name__ == "__main__":
    app.run(debug=True)
