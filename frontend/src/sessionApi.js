const httpClient = {
  async request(url, options = {}) {
    const config = await fetch('/config.json').then(r => r.json());
    const apiBaseUrl = config.apiBaseUrl || 'http://localhost:5000/api';
    
    const requestConfig = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(`${apiBaseUrl}${url}`, requestConfig);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },

  get(url, options = {}) {
    return this.request(url, { method: 'GET', ...options });
  },

  post(url, data, options = {}) {
    return this.request(url, {
      method: 'POST',
      body: JSON.stringify(data),
      ...options,
    });
  }
};

export const sessionApi = {
  createSession: async (sessionData) => {
    return httpClient.post('/sessions', sessionData);
  },

  getSession: async (sessionId) => {
    return httpClient.get(`/sessions/${sessionId}`);
  },

  sendMessage: async (sessionId, message) => {
    return httpClient.post(`/sessions/${sessionId}/message`, { message });
  },

  terminateSession: async (sessionId) => {
    return httpClient.post(`/sessions/${sessionId}/end`);
  },

  getConversation: async (sessionId) => {
    return httpClient.get(`/sessions/${sessionId}/conversation`);
  }
};
