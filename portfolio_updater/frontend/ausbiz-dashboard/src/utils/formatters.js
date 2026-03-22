export const fmt = {
  currency: (n) =>
    new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      maximumFractionDigits: 0,
    }).format(n),

  pct: (n) => `${n > 0 ? '+' : ''}${n.toFixed(1)}%`,

  chartCurrency: (n) => {
    if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`
    if (n >= 1_000)     return `$${(n / 1_000).toFixed(0)}K`
    return `$${n}`
  },
}
