import { ArrowUpRight, ArrowDownRight } from 'lucide-react'

const ACCENT = {
  cyan:    { text: 'text-cyan-400',    bg: 'bg-cyan-400/10',    border: 'border-cyan-500/20'    },
  emerald: { text: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-500/20' },
  rose:    { text: 'text-rose-400',    bg: 'bg-rose-400/10',    border: 'border-rose-500/20'    },
  amber:   { text: 'text-amber-400',   bg: 'bg-amber-400/10',   border: 'border-amber-500/20'   },
}

export default function KpiCard({ label, value, sub, icon: Icon, trend, accent = 'cyan' }) {
  const a = ACCENT[accent]

  return (
    <div className="group bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5
                    backdrop-blur-sm hover:-translate-y-1 transition-all duration-300
                    hover:border-slate-600/60 hover:shadow-xl hover:shadow-slate-900/50">
      <div className="flex items-start justify-between mb-4">
        <div className={`p-2.5 rounded-xl ${a.bg} border ${a.border}`}>
          <Icon className={`w-5 h-5 ${a.text}`} />
        </div>
        {trend !== undefined && (
          <span className={`flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full
                           ${trend >= 0
                              ? 'text-emerald-400 bg-emerald-400/10'
                              : 'text-rose-400 bg-rose-400/10'}`}>
            {trend >= 0
              ? <ArrowUpRight className="w-3 h-3" />
              : <ArrowDownRight className="w-3 h-3" />}
            {Math.abs(trend).toFixed(1)}%
          </span>
        )}
      </div>
      <p className="text-slate-400 text-xs font-medium uppercase tracking-widest mb-1">{label}</p>
      <p className={`text-2xl font-bold tracking-tight ${a.text}`}>{value}</p>
      {sub && <p className="text-slate-500 text-xs mt-1">{sub}</p>}
    </div>
  )
}
