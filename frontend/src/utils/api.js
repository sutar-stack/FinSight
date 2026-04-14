import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || '/api'

/**
 * POST /api/parse
 * @param {string[]} messages
 */
export async function parseMessages(messages) {
  const { data } = await axios.post(`${BASE}/parse`, { messages })
  return data
}

/**
 * POST /api/chat
 * @param {string} message
 * @param {object[]} transactions
 * @param {object[]} history
 */
export async function chatWithCoach(message, transactions = [], history = []) {
  const { data } = await axios.post(`${BASE}/chat`, { message, transactions, history })
  return data
}

/**
 * GET /api/sample
 */
export async function getSamples() {
  const { data } = await axios.get(`${BASE}/sample`)
  return data
}

/**
 * GET /api/health
 */
export async function getHealth() {
  const { data } = await axios.get(`${BASE}/health`)
  return data
}
