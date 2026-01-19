import React, { useState } from "react";
import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

const MedicalTextParser = () => {
  const [text, setText] = useState("");
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);

  const handleIndex = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_URL}/api/`);
      setApiStatus("API is connected: " + response.data);
      console.log(response.data);
    } catch (error) {
      setError("Failed to connect to API: " + error.message);
      console.error("Error connecting to API:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!text.trim()) {
      setError("Please enter some medical text to parse");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setApiStatus(null);
      const response = await axios.post(`${API_URL}/api/parse_medical_text`, {
        medical_text: text,
      });
      console.log(response.data);
      setEntities(response.data.entities || []);
    } catch (error) {
      setError("Error parsing medical text: " + error.message);
      console.error("Error parsing medical text:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setText("");
    setEntities([]);
    setError(null);
    setApiStatus(null);
  };

  const getEntityColor = (label) => {
    const colors = {
      DRUG: "#4CAF50",
      DOSAGE: "#2196F3",
      FREQUENCY: "#FF9800",
      DURATION: "#9C27B0",
      CONDITION: "#F44336",
      PROCEDURE: "#00BCD4",
    };
    return colors[label] || "#757575";
  };

  return (
    <div className="medical-text-parser">
      <div className="parser-container">
        <h1>Medical Text Parser</h1>
        <p className="subtitle">
          Extract structured entities from unstructured medical text
        </p>

        <div className="button-group">
          <button
            onClick={handleIndex}
            disabled={loading}
            className="btn btn-secondary"
          >
            Test API Connection
          </button>
        </div>

        {apiStatus && <div className="status-message success">{apiStatus}</div>}

        <div className="input-section">
          <label htmlFor="medical-text">Enter Medical Text:</label>
          <textarea
            id="medical-text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Example: Metformin 500mg twice daily for diabetes management"
            rows="6"
            disabled={loading}
          />
        </div>

        <div className="button-group">
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="btn btn-primary"
          >
            {loading ? "Parsing..." : "Parse Medical Text"}
          </button>
          <button
            onClick={handleClear}
            disabled={loading}
            className="btn btn-clear"
          >
            Clear
          </button>
        </div>

        {error && <div className="status-message error">{error}</div>}

        {entities.length > 0 && (
          <div className="results-section">
            <h2>Extracted Entities ({entities.length})</h2>
            <div className="entities-grid">
              {entities.map((entity, index) => (
                <div
                  key={index}
                  className="entity-card"
                  style={{ borderLeftColor: getEntityColor(entity[1]) }}
                >
                  <div className="entity-text">{entity[0]}</div>
                  <div
                    className="entity-label"
                    style={{ backgroundColor: getEntityColor(entity[1]) }}
                  >
                    {entity[1]}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MedicalTextParser;
