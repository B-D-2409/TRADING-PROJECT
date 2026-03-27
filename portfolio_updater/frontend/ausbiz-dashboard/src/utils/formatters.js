export const fmt = {
  currency: (n) =>
    new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      maximumFractionDigits: 0,
    }).format(n),

  pct: (n, decimals = 1) => {
    if (n == null || (typeof n === 'number' && isNaN(n))) return '—'
    const num = Number(n)
    if (isNaN(num)) return '—'
    return `${num > 0 ? '+' : ''}${num.toFixed(decimals)}%`
  },

  price: (n) =>
    n == null ? '—' : `$${Number(n).toLocaleString('en-AU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,

  chartCurrency: (n) => {
    if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`
    if (n >= 1_000)     return `$${(n / 1_000).toFixed(0)}K`
    return `$${n}`
  },
}
