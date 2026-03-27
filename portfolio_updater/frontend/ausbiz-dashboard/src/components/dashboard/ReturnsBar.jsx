import { fmt } from '../../utils/formatters'

const PERIODS = [
  { key: 'return3M',  label: '3 Month'  },
  { key: 'return6M',  label: '6 Month'  },
  { key: 'return12M', label: '12 Month' },
  { key: 'ytd',       label: 'YTD'      },
  { key: 'annual',    label: 'Annual'   },
]

function ReturnCard({ label, value }) {
  if (value == null) return null
  const positive = value > 0
  const neutral  = value === 0

  const scheme = neutral
    ? { card: 'bg-slate-800/60 border-slate-700/50 hover:border-slate-600/60',
        label: 'text-slate-500',
        value: 'text-slate-400',
        dot:   'bg-slate-600' }
    : positive
    ? { card: 'bg-emerald-500/5 border-emerald-500/25 hover:bg-emerald-500/10 hover:border-emerald-500/40',
        label: 'text-emerald-600/80',
        value: 'text-emerald-400',
        dot:   'bg-emerald-500' }
    : { card: 'bg-rose-500/5 border-rose-500/25 hover:bg-rose-500/10 hover:border-rose-500/40',
        label: 'text-rose-600/80',
        value: 'text-rose-400',
        dot:   'bg-rose-500' }

  return (
    <div className={`flex-1 flex flex-col justify-between gap-3 rounded-xl px-4 py-3.5
                     border backdrop-blur-sm transition-all duration-200 cursor-default
                     ${scheme.card}`}>
      <div className="flex items-center justify-between">
        <span className={`text-[10px] font-semibold uppercase tracking-widest ${scheme.label}`}>
          {label}
        </span>
        <span className={`w-1.5 h-1.5 rounded-full ${scheme.dot}`} />
      </div>
      <span className={`text-xl font-bold tabular-nums leading-none tracking-tight ${scheme.value}`}>
        {fmt.pct(value)}
      </span>
    </div>
  )
}

export default function ReturnsBar({ returns }) {
  if (!returns) return null

  return (
    <div className="flex gap-3">
      {PERIODS.map(({ key, label }) => (
        <ReturnCard key={key} label={label} value={returns[key]} />
      ))}
    </div>
  )
}
