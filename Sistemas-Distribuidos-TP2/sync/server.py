from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/acesso', methods=['POST'])
def acesso():
    data = request.get_json()
    print(f"Recebido: {data}")
    return jsonify({"status": "COMMITTED"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
