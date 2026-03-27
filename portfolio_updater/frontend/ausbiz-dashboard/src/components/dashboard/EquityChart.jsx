import { useId } from 'react'
import {
  AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { fmt } from '../../utils/formatters'

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const portfolio = payload.find((p) => p.dataKey === 'value')
  const index     = payload.find((p) => p.dataKey === 'indexValue')
  const alpha     = portfolio && index ? portfolio.value - index.value : null

  return (
    <div className="bg-slate-900/95 border border-slate-600/50 rounded-xl p-3.5 shadow-2xl backdrop-blur-sm min-w-[190px]">
      <p className="text-slate-500 text-[10px] font-semibold uppercase tracking-widest mb-2.5">{label}</p>

      {portfolio && (
        <div className="flex items-center justify-between gap-6 mb-1.5">
          <span className="flex items-center gap-1.5 text-xs text-slate-400">
            <span className="inline-block w-2.5 h-0.5 rounded-full bg-emerald-400" />
            Portfolio
          </span>
          <span className="text-emerald-400 text-sm font-bold tabular-nums">
            {fmt.currency(portfolio.value)}
          </span>
        </div>
      )}

      {index && (
        <div className="flex items-center justify-between gap-6 mb-2.5">
          <span className="flex items-center gap-1.5 text-xs text-slate-400">
            <span className="inline-block w-2.5 h-0.5 rounded-full bg-indigo-400 opacity-70"
                  style={{ backgroundImage: 'repeating-linear-gradient(90deg,#818cf8 0,#818cf8 3px,transparent 3px,transparent 6px)', backgroundColor: 'transparent' }} />
            Benchmark
          </span>
          <span className="text-indigo-400 text-sm font-semibold tabular-nums">
            {fmt.currency(index.value)}
          </span>
        </div>
      )}

      {alpha != null && (
        <div className={`flex items-center justify-between pt-2 border-t border-slate-700/60`}>
          <span className="text-[10px] text-slate-500 uppercase tracking-widest">Alpha</span>
          <span className={`text-xs font-bold tabular-nums ${alpha >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {alpha >= 0 ? '+' : ''}{fmt.currency(alpha)}
          </span>
        </div>
      )}
    </div>
  )
}

function ChartLegend({ payload }) {
  if (!payload?.length) return null

  const ordered = [
    payload.find((p) => p.dataKey === 'value'),
    payload.find((p) => p.dataKey === 'indexValue'),
  ].filter(Boolean)

  return (
    <div className="flex items-center justify-end gap-5 pr-2 pb-2">
      {ordered.map((entry) => {
        const isIndex = entry.dataKey === 'indexValue'
        return (
          <span key={entry.dataKey} className="flex items-center gap-2 text-xs text-slate-400">
            {isIndex ? (
              <svg width="18" height="8" className="flex-shrink-0">
                <line x1="0" y1="4" x2="18" y2="4"
                      stroke="#6366f1" strokeWidth="1.5"
                      strokeDasharray="4 3" strokeLinecap="round" />
              </svg>
            ) : (
              <svg width="18" height="8" className="flex-shrink-0">
                <line x1="0" y1="4" x2="18" y2="4"
                      stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" />
              </svg>
            )}
            {isIndex ? 'Benchmark' : 'Portfolio'}
          </span>
        )
      })}
    </div>
  )
}

export default function EquityChart({ data, height = 'h-80', includeIndex = true }) {
  const uid      = useId().replace(/:/g, '')
  const eGrad    = `eq${uid}`
  const iGrad    = `ix${uid}`

  const allValues = data.flatMap((d) => [d.value, includeIndex ? d.indexValue : null].filter(Boolean))
  const minVal    = Math.min(...allValues) * 0.98
  const maxVal    = Math.max(...allValues) * 1.01

  return (
    <div className={`w-full ${height}`}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id={eGrad} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor="#10b981" stopOpacity={0.30} />
              <stop offset="100%" stopColor="#10b981" stopOpacity={0.01} />
            </linearGradient>
            <linearGradient id={iGrad} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor="#6366f1" stopOpacity={0.08} />
              <stop offset="100%" stopColor="#6366f1" stopOpacity={0.01} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />

          <XAxis
            dataKey="date"
            tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'Inter' }}
            axisLine={false}
            tickLine={false}
            dy={8}
          />
          <YAxis
            domain={[minVal, maxVal]}
            tickFormatter={fmt.chartCurrency}
            tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'Inter' }}
            axisLine={false}
            tickLine={false}
            width={72}
          />

          <Tooltip
            content={<ChartTooltip />}
            cursor={{ stroke: '#334155', strokeWidth: 1, strokeDasharray: '4 4' }}
          />
          <Legend verticalAlign="top" align="right" content={<ChartLegend />} />

          {includeIndex && (
            <Area
              type="monotone"
              dataKey="indexValue"
              stroke="#6366f1"
              strokeWidth={1.5}
              strokeDasharray="4 3"
              fill={`url(#${iGrad})`}
              dot={false}
              activeDot={{ r: 4, fill: '#6366f1', stroke: '#1e1b4b', strokeWidth: 2 }}
            />
          )}

          <Area
            type="monotone"
            dataKey="value"
            stroke="#10b981"
            strokeWidth={2.5}
            fill={`url(#${eGrad})`}
            dot={false}
            activeDot={{ r: 5, fill: '#10b981', stroke: '#022c22', strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
