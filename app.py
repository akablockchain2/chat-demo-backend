from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)
db_initialized = False

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        database=os.getenv('DATABASE_NAME', 'chat_db'),
        user=os.getenv('DATABASE_USER', 'chat_user'),
        password=os.getenv('DATABASE_PASSWORD', 'chat_pass'),
        cursor_factory=RealDictCursor
    )

@app.before_request
def initialize_db():
    global db_initialized
    if not db_initialized:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    ip VARCHAR(45),
                    datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message TEXT NOT NULL
                )
            ''')
            conn.commit()
        conn.close()
        db_initialized = True

@app.route('/chat', methods=['PUT'])
def add_message():
    data = request.get_json()
    message = data.get('message')
    ip = request.remote_addr

    if not message:
        return 'Message is required', 400

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('INSERT INTO messages (ip, message) VALUES (%s, %s)', (ip, message))
        conn.commit()
    conn.close()

    return 'Message sent', 201

@app.route('/chat', methods=['GET'])
def get_messages():
    size = request.args.get('size', type=int)
    query = 'SELECT ip, datetime, message FROM messages ORDER BY datetime DESC'
    params = []

    if size and size > 0:
        query += ' LIMIT %s'
        params.append(size)

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        messages = cursor.fetchall()
    conn.close()

    return jsonify(messages)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
