import { Zap, RefreshCw, CircleDot } from 'lucide-react'
import Button from '../common/Button'

const STRATEGY_TABS = [
  { key: 'large_cap', label: 'Large Cap' },
  { key: 'mid_cap',   label: 'Mid Cap'   },
  { key: 'income',    label: 'Income'    },
]

export default function Header({
  activeStrategy,
  onStrategyChange,
  universe,
  lastUpdated,
  onRefresh,
  loading,
}) {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-800/80
                       bg-slate-950/80 backdrop-blur-xl">
      <div className="max-w-screen-2xl mx-auto px-6 py-4 flex flex-wrap items-center gap-4">

        <div className="flex items-center gap-3 mr-auto">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-indigo-600
                          flex items-center justify-center shadow-lg shadow-cyan-500/25">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-white leading-none">
              AusBiz Portfolio Engine
            </h1>
            <p className="text-xs text-slate-500 leading-none mt-0.5">{universe}</p>
          </div>
        </div>

        <nav className="flex items-center gap-1 bg-slate-800/60 border border-slate-700/40
                        rounded-xl p-1 backdrop-blur-sm">
          {STRATEGY_TABS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => onStrategyChange(key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                          ${activeStrategy === key
                            ? 'bg-gradient-to-r from-cyan-500 to-indigo-500 text-white shadow-lg shadow-cyan-500/20'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/40'}`}
            >
              {label}
            </button>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Updated {lastUpdated}</span>
            <span className="flex items-center gap-1.5 ml-1">
              <CircleDot className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-medium">Live</span>
            </span>
          </div>
          <Button variant="ghost" size="sm" onClick={onRefresh} loading={loading}>
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
        </div>

      </div>
    </header>
  )
}
