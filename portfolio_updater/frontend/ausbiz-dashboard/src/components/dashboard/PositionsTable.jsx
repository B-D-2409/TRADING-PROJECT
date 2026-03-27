import { ArrowUpRight, ArrowDownRight } from 'lucide-react'
import { fmt } from '../../utils/formatters'

const CORE_HEADERS = [
  { key: 'ticker',       label: 'Ticker'    },
  { key: 'name',         label: 'Name'      },
  { key: 'sector',       label: 'Sector'    },
  { key: 'shares',       label: 'Shares'    },
  { key: 'entryPrice',   label: 'Entry Px'  },
  { key: 'currentPrice', label: 'Curr Px'   },
  { key: 'profitDollar', label: 'Profit $'  },
  { key: 'profitPct',    label: 'Profit %'  },
]

const FUND_HEADERS = [
  { key: 'pe',          label: 'P/E'      },
  { key: 'divYield',    label: 'Div Yield' },
  { key: 'peg',         label: 'PEG'      },
  { key: 'ps',          label: 'P/S'      },
  { key: 'roe',         label: 'ROE'      },
  { key: 'debtEquity',  label: 'Debt/Eq'  },
]

function safe(v) {
  if (v == null) return null
  const n = Number(v)
  return isNaN(n) ? null : n
}

function fundColor(key, v) {
  if (v == null) return 'text-slate-500'
  switch (key) {
    case 'roe':        return v > 15 ? 'text-emerald-400' : v < 0 ? 'text-rose-400' : 'text-slate-300'
    case 'debtEquity': return v > 2  ? 'text-rose-400'   : v < 0.5 ? 'text-emerald-400' : 'text-slate-300'
    case 'pe':         return v > 30 ? 'text-amber-400'  : v < 15  ? 'text-emerald-400' : 'text-slate-300'
    case 'peg':        return v > 2  ? 'text-amber-400'  : v < 1   ? 'text-emerald-400' : 'text-slate-300'
    case 'divYield':   return v > 0  ? 'text-emerald-400' : 'text-slate-300'
    default:           return 'text-slate-300'
  }
}

function Dash() {
  return <span className="text-slate-600">—</span>
}

function ProfitBadge({ value, pct }) {
  const positive = value >= 0
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full
                     ${positive
                        ? 'bg-emerald-400/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-rose-400/10 text-rose-400 border border-rose-500/20'}`}>
      {positive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
      {fmt.pct(Math.abs(pct))}
    </span>
  )
}

function FundCell({ column, value }) {
  const n = safe(value)
  if (n == null) return <Dash />
  const color = fundColor(column, n)
  let display
  switch (column) {
    case 'divYield': display = fmt.pct(n); break
    case 'roe':      display = fmt.pct(n); break
    default:         display = n.toFixed(2)
  }
  return <span className={`tabular-nums text-xs font-medium ${color}`}>{display}</span>
}

export default function PositionsTable({ positions, detailed = false }) {
  const headers = detailed ? [...CORE_HEADERS, ...FUND_HEADERS] : CORE_HEADERS

  if (!positions?.length) {
    return <p className="text-slate-500 text-sm py-6 text-center">No open positions</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-700/50">
            {headers.map((h, i) => {
              const isFundStart = detailed && i === CORE_HEADERS.length
              return (
                <th
                  key={h.key}
                  className={`text-left text-[10px] font-semibold text-slate-500 uppercase tracking-widest
                               pb-3 pr-4 whitespace-nowrap
                               ${isFundStart ? 'border-l border-slate-700/50 pl-4' : ''}`}
                >
                  {h.label}
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/30">
          {positions.map((pos, i) => {
            const {
              ticker, name, sector, shares,
              entryPrice, currentPrice, profitDollar, profitPct,
              pe, divYield, peg, ps, roe, debtEquity,
            } = pos
            const positive = (safe(profitDollar) ?? 0) >= 0

            return (
              <tr key={i} className="hover:bg-slate-700/20 transition-colors duration-150 cursor-default group">

                <td className="py-3.5 pr-4">
                  <span className="font-bold text-white tracking-wide">{ticker}</span>
                </td>

                <td className="py-3.5 pr-4 text-slate-300 whitespace-nowrap text-xs">{name || <Dash />}</td>

                <td className="py-3.5 pr-4">
                  {sector
                    ? <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-700/60 text-slate-400
                                       border border-slate-600/30 whitespace-nowrap font-medium">
                        {sector}
                      </span>
                    : <Dash />
                  }
                </td>

                <td className="py-3.5 pr-4 text-slate-300 tabular-nums text-xs">
                  {safe(shares) != null ? safe(shares).toLocaleString() : <Dash />}
                </td>

                <td className="py-3.5 pr-4 text-slate-400 tabular-nums text-xs">
                  {safe(entryPrice) != null ? fmt.price(entryPrice) : <Dash />}
                </td>

                <td className="py-3.5 pr-4 tabular-nums text-xs font-semibold">
                  {safe(currentPrice) != null
                    ? <span className={positive ? 'text-emerald-400' : 'text-rose-400'}>
                        {fmt.price(currentPrice)}
                      </span>
                    : <Dash />
                  }
                </td>

                <td className="py-3.5 pr-4 tabular-nums text-xs font-semibold">
                  {safe(profitDollar) != null
                    ? <span className={positive ? 'text-emerald-400' : 'text-rose-400'}>
                        {positive ? '+' : ''}{fmt.currency(profitDollar)}
                      </span>
                    : <Dash />
                  }
                </td>

                <td className="py-3.5 pr-4">
                  {safe(profitDollar) != null && safe(profitPct) != null
                    ? <ProfitBadge value={profitDollar} pct={profitPct} />
                    : <Dash />
                  }
                </td>

                {detailed && (
                  <>
                    <td className="py-3.5 pr-4 border-l border-slate-700/50 pl-4">
                      <FundCell column="pe"         value={pe}         />
                    </td>
                    <td className="py-3.5 pr-4"><FundCell column="divYield"   value={divYield}   /></td>
                    <td className="py-3.5 pr-4"><FundCell column="peg"        value={peg}        /></td>
                    <td className="py-3.5 pr-4"><FundCell column="ps"         value={ps}         /></td>
                    <td className="py-3.5 pr-4"><FundCell column="roe"        value={roe}        /></td>
                    <td className="py-3.5 pr-4"><FundCell column="debtEquity" value={debtEquity} /></td>
                  </>
                )}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
