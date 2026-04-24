from flask import Flask, request, jsonify
from prometheus_client import Counter, Gauge, generate_latest

app = Flask(__name__)

REQUEST_COUNT = Counter('request_count_total', 'Nombre total de requetes')
STUDENT_COUNT = Gauge('student_count', 'Nombre total etudiants')

students = []

@app.route('/')
def home():
    REQUEST_COUNT.inc()
    return "API INPTIC OK"

# ➕ Ajouter étudiant
@app.route('/add_student', methods=['POST'])
def add_student():
    data = request.json
    students.append(data)
    STUDENT_COUNT.set(len(students))
    return jsonify({"message": "Etudiant ajouté", "total": len(students)})

# ➖ Supprimer étudiant
@app.route('/delete_student/<int:index>', methods=['DELETE'])
def delete_student(index):
    if index < len(students):
        students.pop(index)
        STUDENT_COUNT.set(len(students))
        return jsonify({"message": "Etudiant supprimé"})
    return jsonify({"error": "Index invalide"}), 400

# 📊 metrics
@app.route('/metrics')
def metrics():
    return generate_latest()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
