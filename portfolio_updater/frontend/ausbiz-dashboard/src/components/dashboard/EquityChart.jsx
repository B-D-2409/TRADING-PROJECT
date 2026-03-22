import {
  AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { fmt } from '../../utils/formatters'

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-800/95 border border-slate-600/50 rounded-xl p-3 shadow-2xl backdrop-blur-sm">
      <p className="text-slate-400 text-xs font-medium mb-1">{label}</p>
      <p className="text-emerald-400 text-base font-bold">{fmt.currency(payload[0].value)}</p>
    </div>
  )
}

export default function EquityChart({ data, height = 'h-80' }) {
  const minVal = Math.min(...data.map((d) => d.value)) * 0.98
  const maxVal = Math.max(...data.map((d) => d.value)) * 1.01

  return (
    <div className={`w-full ${height}`}>
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
        <defs>
          <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor="#10b981" stopOpacity={0.35} />
            <stop offset="100%" stopColor="#10b981" stopOpacity={0.01} />
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
        <Tooltip content={<ChartTooltip />} cursor={{ stroke: '#334155', strokeWidth: 1 }} />
        <Area
          type="monotone"
          dataKey="value"
          stroke="#10b981"
          strokeWidth={2.5}
          fill="url(#equityGrad)"
          dot={false}
          activeDot={{ r: 5, fill: '#10b981', stroke: '#064e3b', strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
    </div>
  )
}
