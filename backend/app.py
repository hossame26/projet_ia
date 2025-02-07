from flask import Flask, request, jsonify
from flask_cors import CORS
import ollama
import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
from datasets import Dataset


app = Flask(__name__)
CORS(app)

# Initialiser ChromaDB (base de données vectorielle avec persistance)
CHROMADB_PATH = "chromadb_store"
chroma_client = chromadb.PersistentClient(path=CHROMADB_PATH)
collection = chroma_client.get_or_create_collection(name="chatbot_embeddings")

# Charger le modèle d'embedding
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Charger les données depuis un fichier CSV
csv_path = "covid_19_dataset.csv"  # Chemin du fichier CSV

try:
    datasetP = pd.read_csv(csv_path)
    dataset = Dataset.from_pandas(datasetP)  # Convertir en dataset Hugging Face
except FileNotFoundError:
    print(f"!!!!! Erreur : Fichier CSV introuvable ({csv_path})")
    dataset = None

# Ajouter les données dans ChromaDB
def populate_chromadb():
    """ Charge les données du CSV et les insère dans ChromaDB """
    if dataset is None:
        print("!!!!!!! Aucune donnée chargée, ChromaDB ne sera pas mis à jour.")
        return

    print("🚀 Chargement des données depuis le CSV...")

    # Vérification des colonnes du dataset
    if "text" in dataset.column_names:
        texts = dataset["text"]
    elif "abstract" in dataset.column_names:
        texts = dataset["abstract"]
    else:
        print("!!!!!! Aucune colonne 'text' ou 'abstract' trouvée dans le dataset !")
        return

    titles = dataset["title"] if "title" in dataset.column_names else ["Untitled"] * len(texts)

    # Remplacer les valeurs None par ""
    texts = [text if isinstance(text, str) else "" for text in texts]
    titles = [title if isinstance(title, str) else "Untitled" for title in titles]

    # Vérifier que les données ne sont pas déjà enregistrées
    existing_data = collection.get()
    if existing_data and "documents" in existing_data and len(existing_data["documents"]) > 0:
        print("Données déjà présentes dans ChromaDB, pas besoin de recharger.")
        return

    print(f"📊 Encodage des {len(texts)} textes en embeddings...")
    embeddings = model.encode(texts)

    collection.add(
        ids=[str(i) for i in range(len(texts))],
        embeddings=embeddings.tolist(),
        metadatas=[{"title": titles[i]} for i in range(len(titles))],
        documents=texts
    )

    print(" Données chargées dans ChromaDB !")

# Charger les données au démarrage
populate_chromadb()

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "Message vide"}), 400

    # Envoyer la requête à Ollama (DeepSeek)
    response = ollama.chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": user_message}])

    # Vérifier la réponse
    bot_response = response.get("message", {}).get("content", "Erreur : pas de réponse du modèle.")

    return jsonify({"response": bot_response})

@app.route("/debug_chromadb", methods=["GET"])
def debug_chromadb():
    """ Vérifier ce qui est stocké dans ChromaDB """
    stored_data = collection.get()

    if not stored_data or "documents" not in stored_data or len(stored_data["documents"]) == 0:
        return jsonify({"message": "Aucune donnée trouvée dans ChromaDB."})

    return jsonify({"stored_data": stored_data})

@app.route("/clear_chromadb", methods=["POST"])
def clear_chromadb():
    """ Supprime toutes les données de ChromaDB """
    collection.delete(ids=collection.get().get("ids", []))
    return jsonify({"message": "ChromaDB a été vidé."})

@app.route("/search_with_titles", methods=["POST"])
def search_with_titles():
    """ Recherche les documents similaires et affiche les titres """
    data = request.json
    query_text = data.get("text", "").strip()

    if not query_text:
        return jsonify({"error": "Texte vide"}), 400

    print(f"🔍 Recherche de : {query_text}")  # Debugging log

    # Générer l'embedding de la requête
    query_embedding = model.encode([query_text]).tolist()

    # Rechercher les 5 documents les plus proches dans ChromaDB
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=5
    )

    print(f"📊 Résultats de ChromaDB : {results}")  # Debugging log

    if not results or "documents" not in results or not results["documents"]:
        return jsonify({"results": [], "message": "Aucune correspondance trouvée."})

    # Construire la réponse avec titre, texte et score
    response_data = []
    for doc, score, meta in zip(results["documents"][0], results["distances"][0], results["metadatas"][0]):
        if isinstance(meta, list):
            meta = meta[0]  # Fix bug si meta est une liste
        response_data.append({
            "title": meta.get("title", "Untitled"),
            "text": doc,
            "score": score
        })

    return jsonify({"results": response_data})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
