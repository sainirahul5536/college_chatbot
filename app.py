from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from fuzzywuzzy import process, fuzz  # Advanced fuzzy matching

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ✅ Database Configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "college_chatbot"
}

# ✅ Database Connection Function
def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        print("✅ Database connected successfully!")
        return connection
    except mysql.connector.Error as err:
        print(f"❌ Database Connection Error: {err}")
        return None

# ✅ Fetch all patterns from database
def fetch_all_patterns():
    connection = get_db_connection()
    if not connection:
        return []
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT pattern, response FROM faq")
    data = cursor.fetchall()
    cursor.close()
    connection.close()

    return data

# Cache all patterns for fast response
all_patterns = fetch_all_patterns()
print("🔄 Loaded Patterns:", all_patterns)  # Debugging ke liye

@app.route('/')
def home():
    return jsonify({"message": "College Chatbot Backend Running!"})

@app.route('/chat', methods=['POST'])
def chatbot_response():
    try:
        data = request.get_json()
        user_query = data.get("query", "").strip().lower()

        if not user_query:
            return jsonify({"response": "Please enter a valid query."}), 400

        print(f"📝 User Query: {user_query}")

        # ✅ Exact Match Check (First Priority)
        for entry in all_patterns:
            pattern_keywords = entry["pattern"].split('|')
            for keyword in pattern_keywords:
                if user_query == keyword.strip():
                    print(f"✅ Exact Match Found: {keyword}")
                    return jsonify({"response": entry["response"]})

        # ✅ Advanced Fuzzy Matching with Token-Based Comparison
        best_match, score = process.extractOne(user_query, [p["pattern"] for p in all_patterns], scorer=fuzz.token_set_ratio)
        print(f"🔍 Best Match: {best_match}, Score: {score}")

        # ✅ Allowed Topics ke liye fuzzy matching enable
        allowed_topics = ["admission", "fees", "courses", "hostel", "placement", "campus facilities", "scholarships"]
        
        # ✅ Fuzzy matching threshold optimized for better accuracy
        if score > 60 and any(topic in best_match.lower() for topic in allowed_topics):
            for entry in all_patterns:
                if entry["pattern"] == best_match:
                    print(f"✅ Fuzzy Matched Response: {entry['response']}")
                    return jsonify({"response": entry["response"]})

        print("❌ No valid response found!")
        
        # ✅ Irrelevant Queries Ka Proper Response
        irrelevant_queries = ["who is the principal", "how is the weather", "tell me about politics", "who is the president", "tell me a joke"]
        if user_query in irrelevant_queries:
            return jsonify({"response": "I'm sorry, but I can only provide information related to college admissions, courses, fees, and facilities. Please check the official college website for more details."})
        
        return jsonify({"response": "I'm sorry, but I can only provide information related to college admissions, courses, fees, and facilities."})

    except mysql.connector.Error as err:
        print("❌ MySQL Error:", err)
        return jsonify({"response": "Database query failed: " + str(err)}), 500
    except Exception as e:
        print("❌ Error in /chat endpoint:", e)
        return jsonify({"response": "Internal server error: " + str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
