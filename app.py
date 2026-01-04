from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from redis import Redis
from neo4j import GraphDatabase
from cassandra.cluster import Cluster
import logging

app = Flask(__name__)
CORS(app)

# --- 1. DATABASE CONNECTIONS (Using localhost via mapped ports) ---

print("--- Starting NoSQL Connection Checks ---")

try:
    # MongoDB (Port 27017)
    mongo_client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    mongo_db = mongo_client.mini_social
    mongo_client.server_info() # Trigger connection check
    print("✅ MongoDB: Connected")

    # Redis (Port 6379)
    cache = Redis(host='localhost', port=6379, decode_responses=True)
    cache.ping()
    print("✅ Redis: Connected")

    # Neo4j (Port 7687)
    neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password123"))
    with neo4j_driver.session() as session:
        session.run("RETURN 1")
    print("✅ Neo4j: Connected")

    # Cassandra (Port 9042)
    # Pattern B note: Using 127.0.0.1 is usually more stable for Cassandra drivers
    cassandra_cluster = Cluster(['127.0.0.1'], port=9042)
    cassandra_session = cassandra_cluster.connect()
    # Ensure keyspace exists (from your manual step earlier)
    cassandra_session.set_keyspace('social')
    print("✅ Cassandra: Connected")

except Exception as e:
    print(f"❌ Connection Error: {e}")

print("--- All systems ready ---\n")

# --- 2. API ROUTES ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    # Matches your manual insert: email: "frank@email.com"
    user = mongo_db.users.find_one({"email": data['email']}, {"_id": 0})
    if user:
        cache.setex(f"session:{user['username']}", 3600, "active")
        return jsonify(user)
    return jsonify({"error": "Invalid login"}), 401

@app.route('/api/posts', methods=['GET'])
def get_posts():
    posts = list(mongo_db.posts.find({}, {"_id": 0}))
    return jsonify(posts)

@app.route('/api/user/<username>', methods=['GET'])
def get_user(username):
    # Try Redis Cache first
    cached_user = cache.get(f"user_cache:{username}")
    if cached_user:
        return jsonify({"source": "Redis Cache", "data": eval(cached_user)})

    user = mongo_db.users.find_one({"username": username}, {"_id": 0})
    if user:
        cache.setex(f"user_cache:{username}", 300, str(user))
        return jsonify({"source": "MongoDB", "data": user})
    return jsonify({"error": "Not found"}), 404

@app.route('/api/friends/<username>', methods=['GET'])
def get_friends(username):
    with neo4j_driver.session() as session:
        result = session.run(
            "MATCH (u:User {username: $name})-[:FOLLOWS]->(f) RETURN f.username",
            name=username
        )
        friends = [record["f.username"] for record in result]
        return jsonify({"friends": friends})
@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.json
    # Insert into MongoDB
    mongo_db.posts.insert_one({
        "author_id": data['author_id'],
        "content": data['content'],
        "created_at": datetime.datetime.now(),
        "likes_count": 0
    })
    return jsonify({"status": "success"}), 201
    
@app.route('/api/logs/<username>', methods=['GET'])
def get_logs(username):
    query = "SELECT event_time, action FROM activity_log WHERE user_id = %s"
    rows = cassandra_session.execute(query, (username,))
    logs = [{"time": str(r.event_time), "action": r.action} for r in rows]
    return jsonify(logs)

if __name__ == '__main__':
    # Running on 0.0.0.0 so your browser can always find it
    app.run(debug=True, host='0.0.0.0', port=5000)
