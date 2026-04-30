from flask import Flask, request, jsonify
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

app = Flask(__name__)

# ─── CONFIG EMAIL ─────────────────────────────
EMAIL_ADDRESS = "snetmaster2@gmail.com"
EMAIL_PASSWORD = "txrgwoetvgkrzgaw"
RECEIVER_EMAIL = "snetmaster2@gmail.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ─── DATA ────────────────────────────────────
students = []

FILIERES = [
    "Génie Informatique",
    "Génie Réseaux",
    "Génie Électronique",
    "Génie Civil",
    "Management",
    "Data Science"
]

# ─── METRICS ─────────────────────────────────
STUDENT_ADDED = Counter('student_added_total', 'Ajouts')
STUDENT_DELETED = Counter('student_deleted_total', 'Suppressions')
STUDENT_UPDATED = Counter('student_updated_total', 'Modifications')
STUDENT_COUNT = Gauge('student_count', 'Nombre étudiants')
TOTAL_REQUESTS = Counter('total_requests_total', 'Total requêtes', ['type'])

# ─── EMAIL ───────────────────────────────────
def send_notification_email(student_name, operation):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"Notification - {operation}"

        operation_fr = {
            'add': 'AJOUTÉ',
            'delete': 'SUPPRIMÉ',
            'update': 'MODIFIÉ'
        }.get(operation, operation)

        body = f"""
Étudiant : {student_name}
Action : {operation_fr}
Date : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

    except Exception as e:
        print("Erreur email:", e)

# ─── ROUTES ──────────────────────────────────

@app.route('/')
def home():
    return HTML_PAGE

@app.route('/students')
def get_students():
    return jsonify(students)

@app.route('/add_student', methods=['POST'])
def add_student():
    data = request.json

    if not data.get('nom') or not data.get('prenom') or not data.get('filiere'):
        return jsonify({"error": "Champs manquants"}), 400

    student = {
        "nom": data['nom'],
        "prenom": data['prenom'],
        "filiere": data['filiere']
    }

    students.append(student)

    name = f"{student['nom']} {student['prenom']}"
    send_notification_email(name, 'add')

    STUDENT_ADDED.inc()
    TOTAL_REQUESTS.labels(type='add').inc()
    STUDENT_COUNT.set(len(students))

    return jsonify({"message": f"{name} ajouté"})

@app.route('/delete_student/<int:i>', methods=['DELETE'])
def delete_student(i):
    if i < 0 or i >= len(students):
        return jsonify({"error": "Index invalide"}), 400

    student = students.pop(i)
    name = f"{student['nom']} {student['prenom']}"

    send_notification_email(name, 'delete')

    STUDENT_DELETED.inc()
    TOTAL_REQUESTS.labels(type='delete').inc()
    STUDENT_COUNT.set(len(students))

    return jsonify({"message": f"{name} supprimé"})

@app.route('/update_student/<int:i>', methods=['PUT'])
def update_student(i):
    data = request.json

    if i < 0 or i >= len(students):
        return jsonify({"error": "Index invalide"}), 400

    if not data.get('nom') or not data.get('prenom') or not data.get('filiere'):
        return jsonify({"error": "Champs manquants"}), 400

    old = f"{students[i]['nom']} {students[i]['prenom']}"

    students[i] = {
        "nom": data['nom'],
        "prenom": data['prenom'],
        "filiere": data['filiere']
    }

    new = f"{data['nom']} {data['prenom']}"

    send_notification_email(f"{old} → {new}", 'update')

    STUDENT_UPDATED.inc()
    TOTAL_REQUESTS.labels(type='update').inc()

    return jsonify({"message": "Étudiant modifié"})

# ─── METRICS ────────────────────────────────
@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/metrics-values')
def metrics_values():
    return jsonify({
        "added": STUDENT_ADDED._value.get(),
        "deleted": STUDENT_DELETED._value.get(),
        "updated": STUDENT_UPDATED._value.get(),
        "total_requests": (
            STUDENT_ADDED._value.get() +
            STUDENT_DELETED._value.get() +
            STUDENT_UPDATED._value.get()
        ),
        "students_count": len(students)
    })

# ─── DASHBOARD FRONTEND ──────────────────────
HTML_PAGE = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Étudiants INPTIC</title>

<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

.header {
    background: rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(10px);
    text-align: center;
    padding: 25px;
    font-size: 28px;
    font-weight: bold;
    color: white;
    letter-spacing: 1px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

.container {
    max-width: 1300px;
    margin: auto;
    padding: 30px 20px;
}

/* Statistiques */
.stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    cursor: pointer;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 40px rgba(0,0,0,0.3);
}

.card h2 {
    font-size: 2.5em;
    margin: 10px 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.card p {
    color: #666;
    font-size: 0.9em;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
}

/* Formulaires */
.form, .table {
    background: white;
    padding: 30px;
    margin-top: 20px;
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    transition: transform 0.3s ease;
}

.form:hover, .table:hover {
    transform: translateY(-3px);
}

.form h3, .table h3 {
    color: #333;
    margin-bottom: 20px;
    font-size: 1.5em;
    border-left: 4px solid #667eea;
    padding-left: 15px;
}

.form-group {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
}

.input-group {
    position: relative;
}

.input-group label {
    display: block;
    margin-bottom: 5px;
    color: #555;
    font-size: 0.9em;
    font-weight: 600;
}

input, select {
    width: 100%;
    padding: 12px 15px;
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    font-size: 14px;
    transition: all 0.3s ease;
    font-family: inherit;
}

input:focus, select:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.btn-add {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 30px;
    border: none;
    border-radius: 10px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
    width: 100%;
}

.btn-add:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

/* Liste des étudiants */
.student-list {
    max-height: 500px;
    overflow-y: auto;
}

.student {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    background: #f8f9fa;
    margin-top: 10px;
    border-radius: 10px;
    transition: all 0.3s ease;
    border-left: 4px solid #667eea;
}

.student:hover {
    background: #e9ecef;
    transform: translateX(5px);
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.student-info {
    flex: 1;
}

.student-name {
    font-size: 1.1em;
    font-weight: bold;
    color: #333;
}

.student-filiere {
    display: inline-block;
    padding: 4px 12px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 20px;
    font-size: 0.8em;
    margin-top: 5px;
}

.student-actions {
    display: flex;
    gap: 10px;
}

.btn-edit, .btn-del {
    padding: 8px 20px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: bold;
    transition: all 0.3s ease;
}

.btn-edit {
    background: #f59e0b;
    color: white;
}

.btn-edit:hover {
    background: #f39c12;
    transform: translateY(-2px);
    box-shadow: 0 3px 10px rgba(245, 158, 11, 0.3);
}

.btn-del {
    background: #ef4444;
    color: white;
}

.btn-del:hover {
    background: #dc2626;
    transform: translateY(-2px);
    box-shadow: 0 3px 10px rgba(239, 68, 68, 0.3);
}

/* Modal */
.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.7);
    backdrop-filter: blur(5px);
    z-index: 1000;
    justify-content: center;
    align-items: center;
}

.modal-content {
    background: white;
    width: 90%;
    max-width: 500px;
    padding: 30px;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    animation: slideIn 0.3s ease;
}

.modal-content h3 {
    color: #333;
    margin-bottom: 20px;
    font-size: 1.5em;
}

.modal-content input {
    margin-bottom: 15px;
}

.modal-buttons {
    display: flex;
    gap: 10px;
    margin-top: 20px;
}

.modal-buttons button {
    flex: 1;
    padding: 10px;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
}

.modal-buttons button:first-child {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.modal-buttons button:last-child {
    background: #e0e0e0;
    color: #333;
}

.modal-buttons button:hover {
    transform: translateY(-2px);
}

/* Animations */
@keyframes slideIn {
    from {
        transform: translateY(-50px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

/* Scrollbar personnalisée */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #555;
}

/* Responsive */
@media (max-width: 768px) {
    .header {
        font-size: 20px;
        padding: 15px;
    }
    
    .stats {
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 10px;
    }
    
    .card h2 {
        font-size: 1.8em;
    }
    
    .form-group {
        grid-template-columns: 1fr;
    }
    
    .student {
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
    }
    
    .student-actions {
        width: 100%;
        justify-content: flex-end;
    }
    
    .container {
        padding: 15px;
    }
}

/* Loading state */
.loading {
    text-align: center;
    padding: 40px;
    color: #999;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #999;
}

.empty-state svg {
    width: 100px;
    height: 100px;
    margin-bottom: 20px;
    opacity: 0.5;
}
</style>

</head>

<body>

<div class="header">
    🎓 DASHBOARD ÉTUDIANTS INPTIC
</div>

<div class="container">

<div class="stats">
    <div class="card">
        <p>📊 AJOUTS</p>
        <h2 id="a">0</h2>
    </div>
    <div class="card">
        <p>🗑️ SUPPRESSIONS</p>
        <h2 id="d">0</h2>
    </div>
    <div class="card">
        <p>✏️ MODIFICATIONS</p>
        <h2 id="u">0</h2>
    </div>
    <div class="card">
        <p>📈 TOTAL REQUÊTES</p>
        <h2 id="t">0</h2>
    </div>
    <div class="card">
        <p>👨‍🎓 ÉTUDIANTS</p>
        <h2 id="c">0</h2>
    </div>
</div>

<div class="form">
    <h3>➕ Ajouter un étudiant</h3>
    <div class="form-group">
        <div class="input-group">
            <label>Nom</label>
            <input id="nom" type="text" placeholder="Entrez le nom">
        </div>
        <div class="input-group">
            <label>Prénom</label>
            <input id="prenom" type="text" placeholder="Entrez le prénom">
        </div>
        <div class="input-group">
            <label>Filière</label>
            <select id="filiere">
                <option value="">Choisir une filière</option>
                <option>Génie Informatique</option>
                <option>Génie Réseaux</option>
                <option>Génie Électronique</option>
                <option>Génie Civil</option>
                <option>Management</option>
                <option>Data Science</option>
            </select>
        </div>
    </div>
    <button class="btn-add" onclick="add()">
        ✨ AJOUTER L'ÉTUDIANT
    </button>
</div>

<div class="table">
    <h3>📚 Liste des étudiants</h3>
    <div id="list" class="student-list"></div>
</div>

</div>

<!-- Modal modification -->
<div class="modal" id="modal">
    <div class="modal-content">
        <h3>✏️ Modifier l'étudiant</h3>
        <div class="input-group">
            <label>Nom</label>
            <input id="m_nom" type="text" placeholder="Nom">
        </div>
        <div class="input-group">
            <label>Prénom</label>
            <input id="m_prenom" type="text" placeholder="Prénom">
        </div>
        <div class="input-group">
            <label>Filière</label>
            <input id="m_filiere" type="text" placeholder="Filière">
        </div>
        <div class="modal-buttons">
            <button onclick="save()">💾 Enregistrer</button>
            <button onclick="closeM()">❌ Annuler</button>
        </div>
    </div>
</div>

<script>
let index = null;

async function load() {
    let r = await fetch('/students');
    let d = await r.json();
    
    let studentList = document.getElementById('list');
    
    if (d.length === 0) {
        studentList.innerHTML = '<div class="empty-state">📭 Aucun étudiant inscrit</div>';
        return;
    }
    
    let html = '';
    d.forEach((s, i) => {
        html += `
        <div class="student">
            <div class="student-info">
                <div class="student-name">${escapeHtml(s.nom)} ${escapeHtml(s.prenom)}</div>
                <div class="student-filiere">🎓 ${escapeHtml(s.filiere)}</div>
            </div>
            <div class="student-actions">
                <button class="btn-edit" onclick="edit(${i})">✏️ Modifier</button>
                <button class="btn-del" onclick="del(${i})">🗑️ Supprimer</button>
            </div>
        </div>`;
    });
    
    studentList.innerHTML = html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function metrics() {
    let r = await fetch('/metrics-values');
    let d = await r.json();
    
    document.getElementById('a').innerText = d.added;
    document.getElementById('d').innerText = d.deleted;
    document.getElementById('u').innerText = d.updated;
    document.getElementById('t').innerText = d.total_requests;
    document.getElementById('c').innerText = d.students_count;
}

async function add() {
    let nom = document.getElementById('nom').value;
    let prenom = document.getElementById('prenom').value;
    let filiere = document.getElementById('filiere').value;
    
    if (!nom || !prenom || !filiere) {
        alert('⚠️ Veuillez remplir tous les champs');
        return;
    }
    
    await fetch('/add_student', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({nom, prenom, filiere})
    });
    
    document.getElementById('nom').value = '';
    document.getElementById('prenom').value = '';
    document.getElementById('filiere').value = '';
    
    load(); 
    metrics();
}

async function del(i) {
    if (confirm('⚠️ Êtes-vous sûr de vouloir supprimer cet étudiant ?')) {
        await fetch('/delete_student/' + i, {method: 'DELETE'});
        load(); 
        metrics();
    }
}

function edit(i) {
    index = i;
    fetch('/students').then(r => r.json()).then(d => {
        let s = d[i];
        document.getElementById('m_nom').value = s.nom;
        document.getElementById('m_prenom').value = s.prenom;
        document.getElementById('m_filiere').value = s.filiere;
        document.getElementById('modal').style.display = 'flex';
    });
}

async function save() {
    await fetch('/update_student/' + index, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            nom: document.getElementById('m_nom').value,
            prenom: document.getElementById('m_prenom').value,
            filiere: document.getElementById('m_filiere').value
        })
    });
    
    closeM();
    load(); 
    metrics();
}

function closeM() {
    document.getElementById('modal').style.display = 'none';
}

// Chargement initial
load();
metrics();
setInterval(metrics, 5000);

// Fermer le modal en cliquant en dehors
window.onclick = function(event) {
    let modal = document.getElementById('modal');
    if (event.target === modal) {
        closeM();
    }
}
</script>

</body>
</html>
"""

# ─── RUN ─────────────────────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
