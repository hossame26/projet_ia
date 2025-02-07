import React, { useState } from "react";
import "./App.css";

const App = () => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [inputValue, setInputValue] = useState("");
    const [searchResults, setSearchResults] = useState([]);
    const [searchHistory, setSearchHistory] = useState([]);

    // Fonction pour envoyer la requête au backend
    const handleSearch = async () => {
        if (!inputValue.trim()) return; // Ne rien faire si l'input est vide

        // Ajouter la requête à l'historique
        setSearchHistory([...searchHistory, inputValue]);

        // Envoyer la requête à ChromaDB via le backend
        const response = await fetch("http://127.0.0.1:5000/search_with_titles", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: inputValue }),
        });

        const data = await response.json();
        setSearchResults(data.results || []); // Mettre à jour les résultats

        // Effacer l'input après la recherche
        setInputValue("");
    };

    return (
        <div className="container">
            {/* Barre latérale */}
            <div className={`sidebar ${isSidebarOpen ? "open" : "closed"}`}>
                <button className="toggle-btn" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
                    {isSidebarOpen ? "Fermer" : "Ouvrir"}
                </button>
                {isSidebarOpen && <p>Barre Latérale</p>}
            </div>

            {/* Contenu principal */}
            <div className="content">
                <h1>Mon Chatbot</h1>
                <p className="subtitle">Comment puis-je t'aider aujourd'hui ?</p>

                {/* Barre de recherche */}
                <div className="chatbox">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Écrivez un message..."
                    />
                    <button onClick={handleSearch}>Rechercher</button>
                </div>

                {/* Historique des recherches */}
                <div className="history">
                    <h3>Historique des recherches</h3>
                    <ul>
                        {searchHistory.map((query, index) => (
                            <li key={index}>{query}</li>
                        ))}
                    </ul>
                </div>

                {/* Affichage des résultats */}
                <div className="results">
                    <h3>Résultats :</h3>
                    {searchResults.length > 0 ? (
                        searchResults.map((result, index) => (
                            <div key={index} className="result-card">
                                <h4>{result.title}</h4>
                                <p>{result.text}</p>
                                <p className="score">Score : {result.score.toFixed(2)}</p>
                            </div>
                        ))
                    ) : (
                        <p>Aucun résultat trouvé.</p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default App;
