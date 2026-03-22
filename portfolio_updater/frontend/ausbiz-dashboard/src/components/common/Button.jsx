import { Loader2 } from 'lucide-react'

const VARIANTS = {
  primary:   'bg-gradient-to-r from-cyan-500 to-indigo-500 text-white shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30 hover:opacity-90',
  secondary: 'bg-slate-700/60 text-slate-200 border border-slate-600/50 hover:bg-slate-700/80',
  outline:   'bg-transparent text-cyan-400 border border-cyan-500/40 hover:bg-cyan-400/10',
  ghost:     'bg-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-700/40',
}

const SIZES = {
  sm: 'px-3 py-1.5 text-xs rounded-lg',
  md: 'px-4 py-2 text-sm rounded-xl',
  lg: 'px-6 py-3 text-base rounded-xl',
}

export default function Button({
  variant  = 'primary',
  size     = 'md',
  loading  = false,
  disabled = false,
  children,
  className = '',
  ...props
}) {
  return (
    <button
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 font-medium
                  transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed
                  ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...props}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  )
}
