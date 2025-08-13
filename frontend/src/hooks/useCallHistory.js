import { useState, useEffect } from 'react';

export const useCallHistory = () => {
  const [callHistory, setCallHistory] = useState([]);
  const [assignments, setAssignments] = useState([]);

  useEffect(() => {
    // Load from localStorage or API
    const savedHistory = localStorage.getItem('callHistory');
    if (savedHistory) {
      setCallHistory(JSON.parse(savedHistory));
    }
  }, []);

  const addCall = (call) => {
    const newHistory = [...callHistory, call];
    setCallHistory(newHistory);
    localStorage.setItem('callHistory', JSON.stringify(newHistory));
  };

  return {
    callHistory,
    assignments,
    addCall
  };
};
