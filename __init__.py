from flask import Flask, render_template_string, render_template, jsonify, request, redirect, url_for, session
from flask import json
from urllib.request import urlopen
from werkzeug.utils import secure_filename
import sqlite3

# Séquence 5 - Exercice 2 (Protection user/12345)
from functools import wraps
from flask import Response

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Clé secrète pour les sessions


# ----------------------------
# Authentification ADMIN (session)
# ----------------------------
def est_authentifie():
    return session.get('authentifie')


# ----------------------------
# Authentification USER (Basic Auth) - Séquence 5
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
# Routes existantes (Séquence 4/5)
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


# ⚠️ Ces routes CLIENTS ne fonctionneront plus si tu as remplacé schema.sql par la version bibliothèque.
@app.route('/fiche_client/<int:post_id>')
def Readfiche(post_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE id = ?', (post_id,))
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)


@app.route('/fiche_nom/', methods=['GET'])
@require_user_auth
def fiche_nom():
    nom = request.args.get('nom')

    if not nom:
        return "Paramètre 'nom' manquant. Exemple : /fiche_nom/?nom=DUPONT", 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE nom LIKE ?', (f"%{nom}%",))
    data = cursor.fetchall()
    conn.close()

    return render_template('read_data.html', data=data)


@app.route('/consultation/')
def ReadBDD():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients;')
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)


@app.route('/enregistrer_client', methods=['GET'])
def formulaire_client():
    return render_template('formulaire.html')


@app.route('/enregistrer_client', methods=['POST'])
def enregistrer_client():
    nom = request.form['nom']
    prenom = request.form['prenom']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO clients (created, nom, prenom, adresse) VALUES (?, ?, ?, ?)',
        (1002938, nom, prenom, "ICI")
    )
    conn.commit()
    conn.close()
    return redirect('/consultation/')


# ----------------------------
# Séquence 6 - Bibliothèque
# ----------------------------

# 1) Liste de tous les livres
@app.route('/books', methods=['GET'])
def books():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, author, stock FROM books')
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)


# 2) Livres disponibles (stock > 0)
@app.route('/books/available', methods=['GET'])
def books_available():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, author, stock FROM books WHERE stock > 0')
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)


# 3) Ajouter un livre (ADMIN)
@app.route('/books/add', methods=['POST'])
def add_book():
    if not est_authentifie():
        return redirect(url_for('authentification'))

    title = request.form.get('title')
    author = request.form.get('author')
    stock = request.form.get('stock', 1)

    if not title or not author:
        return "Champs manquants: title et author", 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO books (title, author, stock) VALUES (?, ?, ?)',
        (title, author, int(stock))
    )
    conn.commit()
    conn.close()
    return "Livre ajouté"


# 4) Supprimer un livre (ADMIN)
@app.route('/books/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if not est_authentifie():
        return redirect(url_for('authentification'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
    conn.commit()
    conn.close()
    return "Livre supprimé"


# 5) Emprunter un livre (USER user/12345)
@app.route('/loan/<int:book_id>', methods=['POST'])
@require_user_auth
def loan_book(book_id):
    conn = sqlite3.connect('database.db')
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


# 6) Retourner un livre (USER user/12345)
@app.route('/return/<int:book_id>', methods=['POST'])
@require_user_auth
def return_book(book_id):
    conn = sqlite3.connect('database.db')
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


if __name__ == "__main__":
    app.run(debug=True)
