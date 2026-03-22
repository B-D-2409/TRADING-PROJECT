export function Heading({ children, className = '', as: Tag = 'h2' }) {
  return (
    <Tag className={`text-base font-semibold text-white leading-snug ${className}`}>
      {children}
    </Tag>
  )
}

export function SubText({ children, className = '' }) {
  return (
    <p className={`text-xs text-slate-500 mt-0.5 ${className}`}>
      {children}
    </p>
  )
}

export function MoneyText({ value, format, className = '' }) {
  const positive  = value >= 0
  const displayed = format ? format(value) : value
  return (
    <span className={`${positive ? 'text-emerald-400' : 'text-rose-400'} ${className}`}>
      {displayed}
    </span>
  )
}
