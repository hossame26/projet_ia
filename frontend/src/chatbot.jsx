import { useState } from "react";

export default function Chatbot() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");

    const sendMessage = async () => {
        if (!input) return;
    
        const userMessage = { sender: "user", text: input };
        setMessages([...messages, userMessage]);
    
        const response = await fetch("http://localhost:5000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: input })
        });
    
        const data = await response.json();
        setMessages([...messages, userMessage, { sender: "bot", text: data.response }]);
    
        setInput("");
    };
    

    return (
        <div className="chat-container">
            <div className="chatbox">
                {messages.map((msg, index) => (
                    <p key={index} className={msg.sender === "user" ? "user-message" : "bot-message"}>
                        <strong>{msg.sender === "user" ? "Vous" : "Bot"} :</strong> {msg.text}
                    </p>
                ))}
            </div>
            <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Écrivez un message..." />
            <button onClick={sendMessage}>Envoyer</button>
        </div>
    );
}
