from flask import Flask, request, jsonify
import pymysql
import hashlib
import os

app = Flask(__name__)

def get_db():
    return pymysql.connect(
        host=os.environ.get('MYSQLHOST', 'localhost'),
        user=os.environ.get('MYSQLUSER', 'avnadmin'),
        password=os.environ.get('MYSQLPASSWORD'),
        database=os.environ.get('MYSQLDATABASE', 'defaultdb'),
        port=int(os.environ.get('MYSQLPORT', 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )

# --- LOGIN ---
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    pw_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, username, role, points FROM user WHERE username=%s AND password_hash=%s",
                (data['username'], pw_hash))
    user = cur.fetchone()
    db.close()
    if user:
        return jsonify({"success": True, "user": user})
    return jsonify({"success": False, "message": "Falsche Zugangsdaten"}), 401

# --- PUNKTE ANZEIGEN ---
@app.route('/punkte/<int:user_id>', methods=['GET'])
def punkte(user_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT points FROM user WHERE id=%s", (user_id,))
    result = cur.fetchone()
    db.close()
    return jsonify(result)

# --- GUTSCHEINE ANZEIGEN ---
@app.route('/gutscheine', methods=['GET'])
def gutscheine():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM gifts WHERE active=1")
    result = cur.fetchall()
    db.close()
    return jsonify(result)

# --- GUTSCHEIN EINLÖSEN ---
@app.route('/einloesen', methods=['POST'])
def einloesen():
    data = request.json
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT points FROM user WHERE id=%s", (data['student_id'],))
    user = cur.fetchone()
    cur.execute("SELECT cost FROM gifts WHERE id=%s", (data['gift_id'],))
    gift = cur.fetchone()
    if user['points'] < gift['cost']:
        db.close()
        return jsonify({"success": False, "message": "Nicht genug Punkte"}), 400
    cur.execute("UPDATE user SET points=points-%s WHERE id=%s", (gift['cost'], data['student_id']))
    cur.execute("INSERT INTO redemptions (student_id, gift_id) VALUES (%s, %s)",
                (data['student_id'], data['gift_id']))
    db.commit()
    db.close()
    return jsonify({"success": True})

# --- PUNKTE VERGEBEN (nur Lehrer) ---
@app.route('/punkte/vergeben', methods=['POST'])
def vergeben():
    data = request.json
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE user SET points=points+%s WHERE id=%s", (data['punkte'], data['student_id']))
    cur.execute("INSERT INTO point_history (student_id, teacher_id, points_swap, reason) VALUES (%s,%s,%s,%s)",
                (data['student_id'], data['teacher_id'], data['punkte'], data['grund']))
    db.commit()
    db.close()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
