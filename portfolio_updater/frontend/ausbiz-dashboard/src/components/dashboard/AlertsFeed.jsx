import { Bell, ArrowUpRight, ArrowDownRight, ChevronRight } from 'lucide-react'

function AlertBadge({ action }) {
  return action === 'BUY' ? (
    <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1
                     bg-emerald-400/15 text-emerald-400 border border-emerald-500/30 rounded-full">
      <ArrowUpRight className="w-3 h-3" /> BUY
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1
                     bg-rose-400/15 text-rose-400 border border-rose-500/30 rounded-full">
      <ArrowDownRight className="w-3 h-3" /> SELL
    </span>
  )
}

export default function AlertsFeed({ alerts }) {
  if (!alerts?.length) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-slate-500 py-8">
        <Bell className="w-10 h-10 opacity-30" />
        <p className="text-sm">No alerts this week</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {alerts.map(({ ticker, action, date, reason }, i) => (
        <div
          key={i}
          className="group flex items-center gap-3 p-3 rounded-xl bg-slate-700/20 border border-slate-700/30
                     hover:bg-slate-700/40 hover:border-slate-600/40 transition-all duration-200 cursor-default"
        >
          <div className={`w-1.5 h-10 rounded-full flex-shrink-0
                          ${action === 'BUY' ? 'bg-emerald-500' : 'bg-rose-500'}`} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-white text-sm font-semibold">{ticker}</span>
              <AlertBadge action={action} />
            </div>
            <p className="text-slate-400 text-xs truncate">{reason}</p>
          </div>
          <div className="text-right flex-shrink-0">
            <p className="text-slate-500 text-xs">{date}</p>
            <ChevronRight className="w-3.5 h-3.5 text-slate-600 mt-1 ml-auto
                                     group-hover:text-slate-400 transition-colors" />
          </div>
        </div>
      ))}
    </div>
  )
}
