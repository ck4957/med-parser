import React, { useState } from 'react';
import axios from 'axios';
const API_URL = process.env.REACT_APP_API_URL;



const MedicalTextParser = () => {
  const [text, setText] = useState('');

  const handleIndex = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/`);
      console.log(response.data);
    } catch (error) {
      console.error('Error parsing medical text:', error);
    }
  };

  const handleSubmit = async () => {
    try {
      const response = await axios.post(`${API_URL}/api/parse_medical_text`, { medical_text: text });
      console.log(response.data);
    } catch (error) {
      console.error('Error parsing medical text:', error);
    }
  };

  return (
    <div>
      <textarea value={text} onChange={(e) => setText(e.target.value)} />
      <button onClick={handleSubmit}>Parse Medical Text</button>
      <button onClick={handleIndex}>Index</button>
    </div>
  );
};

export default MedicalTextParser;