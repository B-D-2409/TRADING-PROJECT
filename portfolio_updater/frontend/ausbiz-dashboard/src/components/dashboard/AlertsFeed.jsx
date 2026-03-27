import { Bell, ArrowUpRight, ArrowDownRight, TrendingUp, TrendingDown } from 'lucide-react'
import { fmt } from '../../utils/formatters'

function safe(v) {
  if (v == null) return null
  const n = Number(v)
  return isNaN(n) ? null : n
}

function AlertBadge({ action }) {
  return action === 'BUY' ? (
    <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5
                     bg-emerald-400/15 text-emerald-400 border border-emerald-500/30 rounded-full
                     uppercase tracking-wide">
      <ArrowUpRight className="w-3 h-3" /> BUY
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5
                     bg-rose-400/15 text-rose-400 border border-rose-500/30 rounded-full
                     uppercase tracking-wide">
      <ArrowDownRight className="w-3 h-3" /> SELL
    </span>
  )
}

function SectorBadge({ sector }) {
  if (!sector) return null
  return (
    <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-700/60 text-slate-400
                     border border-slate-600/30 font-medium whitespace-nowrap">
      {sector}
    </span>
  )
}

function DiffBadge({ value, action }) {
  if (safe(value) == null) return null
  const isGoodSignal = (action === 'BUY' && value >= 0) || (action === 'SELL' && value < 0)
  const Icon = isGoodSignal ? TrendingUp : TrendingDown
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full
                      ${isGoodSignal
                        ? 'bg-emerald-400/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-rose-400/10 text-rose-400 border border-rose-500/20'}`}>
      <Icon className="w-3 h-3" />
      {value >= 0 ? '+' : ''}{value.toFixed(2)}%
    </span>
  )
}

function PriceStack({ label, value }) {
  const n = safe(value)
  return (
    <div className="flex flex-col items-end gap-0.5 min-w-[56px]">
      <span className="text-[10px] text-slate-600 font-medium uppercase tracking-wide">{label}</span>
      <span className="text-slate-200 text-xs font-semibold tabular-nums">
        {n != null ? fmt.price(n) : '—'}
      </span>
    </div>
  )
}

export default function AlertsFeed({ alerts, detailed = true }) {
  if (!alerts?.length) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-slate-500 py-10">
        <Bell className="w-10 h-10 opacity-20" />
        <p className="text-sm">No alerts this week</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {alerts.map(({ ticker, action, date, reason, sector, alertPrice, currentPrice, difference }, i) => (
        <div
          key={i}
          className="group flex items-stretch gap-3 px-4 py-3.5 rounded-xl
                     bg-slate-700/20 border border-slate-700/30
                     hover:bg-slate-700/35 hover:border-slate-600/40
                     transition-all duration-200 cursor-default"
        >
          <div className={`w-1 rounded-full flex-shrink-0 self-stretch
                          ${action === 'BUY' ? 'bg-emerald-500' : 'bg-rose-500'}`} />

          <div className="flex-1 min-w-0 flex flex-col gap-2">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-white text-sm font-bold tracking-wide">{ticker}</span>
              <AlertBadge action={action} />
              <SectorBadge sector={sector} />
              <span className="text-slate-600 text-[10px] ml-auto flex-shrink-0">{date}</span>
            </div>

            <div className="flex items-center justify-between gap-3">
              <p className="text-slate-500 text-xs leading-snug truncate">{reason}</p>
              {detailed && (
                <DiffBadge value={difference} action={action} />
              )}
            </div>
          </div>

          {detailed && (
            <div className="flex items-center gap-4 flex-shrink-0 pl-3 border-l border-slate-700/40">
              <PriceStack label="Alert Px" value={alertPrice}   />
              <PriceStack label="Curr Px"  value={currentPrice} />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
