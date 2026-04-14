/**
 * Format a number as Indian currency
 * @param {number} amount
 * @returns {string}  e.g. "₹1,23,456.78"
 */
export function formatINR(amount) {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(amount)
}

/**
 * Format a date string to readable form
 * @param {string} dateStr  e.g. "2024-04-12"
 * @returns {string}        e.g. "12 Apr 2024"
 */
export function formatDate(dateStr) {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
  } catch {
    return dateStr
  }
}

/**
 * Truncate text with ellipsis
 */
export function truncate(str, n = 60) {
  return str && str.length > n ? str.slice(0, n) + '…' : str
}

/**
 * Delay helper
 */
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
