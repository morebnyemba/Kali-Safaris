import React from 'react';
import { Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart } from 'recharts';
import { FiLoader, FiBarChart2 } from 'react-icons/fi';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="p-2 bg-background border rounded-md shadow-lg text-sm">
        <p className="font-bold mb-1">{label}</p>
        <p className="text-blue-500">{`New Contacts: ${payload[0].value}`}</p>
      </div>
    );
  }
  return null;
};

export default function EngagementTrendChart({ data, isLoading }) {
  if (isLoading) return <div className="flex items-center justify-center h-full"><FiLoader className="animate-spin h-8 w-8 text-muted-foreground" /></div>;
  if (!data || data.length === 0) return <div className="flex items-center justify-center h-full text-muted-foreground"><FiBarChart2 className="mr-2" />No data for this period.</div>;

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
        <defs>
          <linearGradient id="colorEngagement" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis dataKey="period" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} tickLine={{ stroke: 'hsl(var(--muted-foreground))' }} />
        <YAxis allowDecimals={false} stroke="hsl(var(--muted-foreground))" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--muted))' }} />
        <Area type="monotone" dataKey="new_contacts" name="New Contacts" stroke="hsl(var(--primary))" fillOpacity={1} fill="url(#colorEngagement)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}