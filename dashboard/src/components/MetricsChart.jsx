import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line
} from 'recharts';
import { Activity, TrendingDown, TrendingUp } from 'lucide-react';

export const MetricsChart = ({ data = [], lossData = [] }) => {
  // Map raw floats to charted objects.
  const chartData = data.length > 0 
    ? data.map((val, index) => ({
        round: index + 1,
        accuracy: (val * 100).toFixed(1),
        loss: (lossData[index] || 0).toFixed(3),
      }))
    : [{ round: 0, accuracy: 0, loss: 0 }];

  const currentAcc = data.length > 0 ? (data[data.length - 1] * 100).toFixed(1) : "0.0";
  const currentLoss = lossData.length > 0 ? lossData[lossData.length - 1].toFixed(3) : "0.000";
  
  const accImproved = data.length > 1 ? data[data.length-1] >= data[data.length-2] : true;
  const lossReduced = lossData.length > 1 ? lossData[lossData.length-1] <= lossData[lossData.length-2] : true;

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex items-center justify-between mb-6 pb-3 border-b border-border shrink-0">
        <div className="flex items-center gap-2">
          <Activity size={12} className="text-primary" />
          <span className="text-[10px] font-bold text-text-main uppercase tracking-widest">
            Institutional Convergence Metrics
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 bg-emerald-50 border border-emerald-100/50">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span className="text-[9px] font-extrabold text-emerald-800 uppercase tracking-widest tabular-nums">
              {currentAcc}%
            </span>
          </div>
        </div>
      </div>

      <div className="h-[240px] w-full min-h-[240px] relative overflow-hidden" style={{ minWidth: 0 }}>
        <ResponsiveContainer width="99%" height="100%" debounce={50}>
          <AreaChart
            data={chartData}
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorAcc" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.15} />
                <stop offset="95%" stopColor="var(--primary)" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorLoss" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.1} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.5} />
            <XAxis
              dataKey="round"
              fontSize={10}
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'var(--text-muted)', fontWeight: 600, fontFamily: 'monospace' }}
              dy={10}
            />
            <YAxis
              yAxisId="left"
              fontSize={10}
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'var(--text-muted)', fontWeight: 600, fontFamily: 'monospace' }}
              domain={[0, 100]}
              tickFormatter={(val) => `${val}%`}
              dx={-5}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              fontSize={10}
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#ef4444', fontWeight: 600, fontFamily: 'monospace' }}
              dx={5}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid var(--border)',
                borderRadius: '0px',
                fontSize: '11px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                fontFamily: 'monospace'
              }}
              labelStyle={{ color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}
              itemStyle={{ fontWeight: 700 }}
            />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="accuracy"
              stroke="var(--primary)"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorAcc)"
              animationDuration={1500}
              name="Accuracy"
            />
            <Area
              yAxisId="right"
              type="monotone"
              dataKey="loss"
              stroke="#ef4444"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorLoss)"
              animationDuration={1500}
              name="Loss"
              strokeDasharray="4 4"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 gap-8 mt-10">
        <div className="p-6 bg-white border border-border shadow-sm">
          <div className="flex flex-col gap-3">
            <span className="type-label text-text-muted opacity-70">Global Accuracy</span>
            <div className="flex items-baseline gap-2">
               <span className="type-l2 sans text-text-main tabular-nums">{currentAcc}%</span>
               {data.length > 1 && (
                 <TrendingUp size={14} className={accImproved ? 'text-emerald-500' : 'text-error rotate-180'} />
               )}
            </div>
          </div>
          <div className="text-[10px] font-bold uppercase tracking-widest mt-4 text-text-muted">
            Institutional Convergence
          </div>
        </div>
        
        <div className="p-6 bg-white border border-border shadow-sm">
          <div className="flex flex-col gap-3">
            <span className="type-label text-text-muted opacity-70">Training Loss</span>
            <div className="flex items-baseline gap-2">
               <span className="type-l2 sans text-error tabular-nums">{currentLoss}</span>
               {lossData.length > 1 && (
                 <TrendingDown size={14} className={lossReduced ? 'text-emerald-500' : 'text-error rotate-180'} />
               )}
            </div>
          </div>
          <div className="text-[10px] font-bold uppercase tracking-widest mt-4 text-text-muted">
            Error Minimization
          </div>
        </div>
      </div>
    </div>
  );
};
