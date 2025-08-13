import { httpClient } from './httpClient';

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
