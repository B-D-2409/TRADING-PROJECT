import { useState, useRef, useEffect } from 'react'
import { Terminal, Loader2, CheckCircle2, XCircle, ChevronDown, Play } from 'lucide-react'
import { runTradingEngine } from '../../api/portfolioApi'

const STRATEGIES = [
  { key: 'all',       label: 'All Strategies' },
  { key: 'large_cap', label: 'Large Cap'       },
  { key: 'mid_cap',   label: 'Mid Cap'         },
  { key: 'income',    label: 'Income'          },
]

const RUN_TYPES = [
  { key: 'daily',   label: 'Daily Run'   },
  { key: 'weekly',  label: 'Weekly Run'  },
  { key: 'monthly', label: 'Monthly Run' },
]

export default function EngineControl() {
  const [open,     setOpen]     = useState(false)
  const [strategy, setStrategy] = useState('all')
  const [status,   setStatus]   = useState(null)   // null | 'running' | 'success' | 'error'
  const [message,  setMessage]  = useState('')
  const panelRef = useRef(null)

  useEffect(() => {
    if (!open) return
    function onOutsideClick(e) {
      if (panelRef.current && !panelRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onOutsideClick)
    return () => document.removeEventListener('mousedown', onOutsideClick)
  }, [open])

  async function handleRun(runType) {
    setStatus('running')
    setMessage('')
    try {
      const res = await runTradingEngine(strategy, runType)
      setStatus('success')
      setMessage(res.data.message || 'Engine run completed successfully.')
    } catch (err) {
      setStatus('error')
      const detail = err?.response?.data?.detail
      if (detail && typeof detail === 'object') {
        setMessage(detail.message || 'Engine run failed.')
      } else {
        setMessage(typeof detail === 'string' ? detail : 'Engine run failed.')
      }
    }
  }

  const isRunning = status === 'running'

  return (
    <div className="relative" ref={panelRef}>

      {/* Trigger button */}
      <button
        onClick={() => { setOpen(o => !o) }}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                    transition-all duration-200 border
                    ${open
                      ? 'bg-cyan-500/15 border-cyan-500/40 text-cyan-400 shadow-sm shadow-cyan-500/10'
                      : 'bg-slate-800/60 border-slate-700/40 text-slate-400 hover:text-slate-200 hover:border-slate-600/60'
                    }`}
      >
        <Terminal className="w-3.5 h-3.5" />
        <span>Update Portfolio</span>
        <ChevronDown className={`w-3 h-3 transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
      </button>

      {/* Popover panel */}
      {open && (
        <div className="absolute right-0 top-full mt-2 w-72 z-[60]
                        bg-slate-900/95 backdrop-blur-xl border border-slate-700/60
                        rounded-2xl shadow-2xl shadow-slate-950/80 p-4 space-y-4">

          {/* Panel header */}
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500 to-indigo-600
                            flex items-center justify-center shadow-md shadow-cyan-500/20 flex-shrink-0">
              <Terminal className="w-3.5 h-3.5 text-white" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white leading-none">Run Portfolio Update</p>
              <p className="text-[10px] text-slate-500 mt-0.5">Execute trading workflows</p>
            </div>
          </div>

          {/* Divider */}
          <div className="border-t border-slate-800/80" />

          {/* Strategy selector */}
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 mb-2">
              Target Strategy
            </p>
            <div className="grid grid-cols-2 gap-1.5">
              {STRATEGIES.map(({ key, label }) => (
                <button
                  key={key}
                  disabled={isRunning}
                  onClick={() => setStrategy(key)}
                  className={`px-2.5 py-2 rounded-lg text-xs font-medium transition-all duration-150 border
                              ${strategy === key
                                ? 'bg-cyan-500/15 border-cyan-500/40 text-cyan-300'
                                : 'bg-slate-800/60 border-slate-700/40 text-slate-400 hover:text-slate-200 hover:border-slate-600/60'
                              }
                              disabled:opacity-40 disabled:cursor-not-allowed`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Run type buttons */}
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 mb-2">
              Workflow
            </p>
            <div className="flex flex-col gap-1.5">
              {RUN_TYPES.map(({ key, label }) => (
                <button
                  key={key}
                  disabled={isRunning}
                  onClick={() => handleRun(key)}
                  className="group flex items-center justify-between px-3 py-2.5 rounded-xl
                             bg-gradient-to-r from-cyan-500/8 to-indigo-500/8
                             border border-cyan-500/20 text-cyan-300 text-xs font-medium
                             hover:border-cyan-500/40 hover:from-cyan-500/15 hover:to-indigo-500/15
                             hover:text-cyan-200 transition-all duration-150
                             disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <span>{label}</span>
                  <Play className="w-3 h-3 opacity-40 group-hover:opacity-80 transition-opacity" />
                </button>
              ))}
            </div>
          </div>

          {/* Status feedback */}
          {isRunning && (
            <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl
                            bg-indigo-500/10 border border-indigo-500/25">
              <Loader2 className="w-4 h-4 text-indigo-400 animate-spin flex-shrink-0" />
              <div>
                <p className="text-xs font-medium text-indigo-300">Engine is running…</p>
                <p className="text-[10px] text-slate-500 mt-0.5">Do not close this window.</p>
              </div>
            </div>
          )}

          {status === 'success' && (
            <div className="flex items-start gap-2.5 px-3 py-2.5 rounded-xl
                            bg-emerald-500/10 border border-emerald-500/25">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-emerald-300 leading-relaxed">{message}</p>
            </div>
          )}

          {status === 'error' && (
            <div className="flex items-start gap-2.5 px-3 py-2.5 rounded-xl
                            bg-rose-500/10 border border-rose-500/25">
              <XCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-rose-300 leading-relaxed">{message}</p>
            </div>
          )}

        </div>
      )}
    </div>
  )
}
