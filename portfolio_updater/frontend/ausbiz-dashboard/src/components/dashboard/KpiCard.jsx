import { ArrowUpRight, ArrowDownRight } from 'lucide-react'

const ACCENT = {
  cyan:    { text: 'text-cyan-400',    bg: 'bg-cyan-400/10',    border: 'border-cyan-500/20',    bar: 'bg-cyan-500/50',    glow: 'hover:shadow-cyan-500/10'    },
  emerald: { text: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-500/20', bar: 'bg-emerald-500/50', glow: 'hover:shadow-emerald-500/10' },
  rose:    { text: 'text-rose-400',    bg: 'bg-rose-400/10',    border: 'border-rose-500/20',    bar: 'bg-rose-500/50',    glow: 'hover:shadow-rose-500/10'    },
  amber:   { text: 'text-amber-400',   bg: 'bg-amber-400/10',   border: 'border-amber-500/20',   bar: 'bg-amber-500/50',   glow: 'hover:shadow-amber-500/10'   },
}

export default function KpiCard({ label, value, sub, icon: Icon, trend, accent = 'cyan' }) {
  const a = ACCENT[accent]

  return (
    <div className={`group relative overflow-hidden bg-slate-800/50 border border-slate-700/50
                    rounded-2xl p-5 backdrop-blur-sm transition-all duration-300
                    hover:-translate-y-1 hover:border-slate-600/60
                    hover:shadow-xl hover:shadow-slate-900/50 ${a.glow}`}>
      <div className={`absolute top-0 left-0 right-0 h-px ${a.bar}`} />

      <div className="flex items-start justify-between mb-4">
        <div className={`p-2.5 rounded-xl ${a.bg} border ${a.border}
                         group-hover:scale-110 transition-transform duration-300`}>
          <Icon className={`w-5 h-5 ${a.text}`} />
        </div>
        {trend !== undefined && (
          <span className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full
                           ${trend >= 0
                              ? 'text-emerald-400 bg-emerald-400/10 border border-emerald-500/20'
                              : 'text-rose-400 bg-rose-400/10 border border-rose-500/20'}`}>
            {trend >= 0
              ? <ArrowUpRight className="w-3 h-3" />
              : <ArrowDownRight className="w-3 h-3" />}
            {Math.abs(trend).toFixed(1)}%
          </span>
        )}
      </div>

      <p className="text-slate-500 text-[10px] font-semibold uppercase tracking-widest mb-1.5">{label}</p>
      <p className={`text-2xl font-bold tracking-tight leading-none ${a.text}`}>{value}</p>
      {sub && <p className="text-slate-500 text-xs mt-2 leading-snug">{sub}</p>}
    </div>
  )
}
