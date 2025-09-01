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

from fastapi import FastAPI, HTTPException
import psycopg2, os
from psycopg2.extras import RealDictCursor

app = FastAPI()

def get_db():
    return psycopg2.connect(
        os.environ["DATABASE_URL"],
        sslmode="require",
        cursor_factory=RealDictCursor
    )

# --- /markets ---
@app.get("/markets")
def get_markets():
    with get_db() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM markets;")
        return cur.fetchall()

# --- /balances/{user_id} ---
@app.get("/balances/{user_id}")
def get_balances(user_id: int):
    with get_db() as conn, conn.cursor() as cur:
        cur.execute("SELECT asset, amount FROM balances WHERE user_id=%s;", (user_id,))
        balances = cur.fetchall()
        if not balances:
            raise HTTPException(status_code=404, detail="User not found or no balances")
        return balances

# --- /trades ---
@app.post("/trades")
def place_trade(order: dict):
    user_id = order["user_id"]
    market  = order["market"]
    side    = order["side"]
    price   = order["price"]
    qty     = order["qty"]

    with get_db() as conn, conn.cursor() as cur:
        # insert order
        cur.execute("""
            INSERT INTO orders (user_id, market, side, price, qty)
            VALUES (%s, %s, %s, %s, %s) RETURNING id;
        """, (user_id, market, side, price, qty))
        order_id = cur.fetchone()["id"]

        # simulate trade (skeleton only)
        cur.execute("""
            INSERT INTO trades (market, price, qty, side, user_id)
            VALUES (%s, %s, %s, %s, %s);
        """, (market, price, qty, side, user_id))

        # update balances (basic skeleton)
        if side == "buy":
            cur.execute("UPDATE balances SET amount = amount - %s WHERE user_id=%s AND asset='USD';", (price*qty, user_id))
            cur.execute("UPDATE balances SET amount = amount + %s WHERE user_id=%s AND asset='BTC';", (qty, user_id))
        elif side == "sell":
            cur.execute("UPDATE balances SET amount = amount - %s WHERE user_id=%s AND asset='BTC';", (qty, user_id))
            cur.execute("UPDATE balances SET amount = amount + %s WHERE user_id=%s AND asset='USD';", (price*qty, user_id))

        conn.commit()
        return {"order_id": order_id, "status": "ok"}

