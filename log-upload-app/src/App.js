import React, { useState } from "react";

function App() {
  const [log, setLog] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const API_URL = "https://5ulq8h8vi4.execute-api.ap-south-2.amazonaws.com/logs";

  const handleSubmit = async () => {
    try {
      setMessage("");
      setError("");

      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ log }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(
          `✅ ${data.message} | Severity: ${data.severity}`
        );
      } else {
        setError("❌ Something went wrong");
      }
    } catch (err) {
      console.error(err);
      setError("❌ Failed to connect to API");
    }
  };

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1>Log Upload Interface</h1>

      <input
        type="text"
        value={log}
        onChange={(e) => setLog(e.target.value)}
        placeholder="Enter log..."
        style={{ width: "300px", marginRight: "10px" }}
      />

      <button onClick={handleSubmit}>Submit</button>

      <div style={{ marginTop: "20px" }}>
        {message && <p style={{ color: "green" }}>{message}</p>}
        {error && <p style={{ color: "red" }}>{error}</p>}
      </div>
    </div>
  );
}

export default App;