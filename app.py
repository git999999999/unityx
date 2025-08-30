# app.py
from flask import Flask, request, jsonify
import os
import psycopg2

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

@app.route("/orders", methods=["POST"])
def create_order():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO public.orders (market, side, price, qty) VALUES (%s,%s,%s,%s) RETURNING id",
        (data["market"], data["side"], data["price"], data["qty"])
    )
    order_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok", "order_id": order_id})

@app.route("/orders", methods=["GET"])
def list_orders():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, market, side, price, qty, ts FROM public.orders ORDER BY ts DESC LIMIT 20")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([
        {
            "id": r[0],
            "market": r[1],
            "side": r[2],
            "price": float(r[3]),
            "qty": float(r[4]),
            "ts": str(r[5])
        } for r in rows
    ])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

