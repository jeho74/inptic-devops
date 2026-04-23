from flask import Flask
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Compteur de requêtes
REQUEST_COUNT = Counter('request_count', 'Nombre total de requetes', ['endpoint'])

@app.route('/')
def home():
    REQUEST_COUNT.labels(endpoint='/').inc()
    return 'Bienvenue sur l application INPTIC!'

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
