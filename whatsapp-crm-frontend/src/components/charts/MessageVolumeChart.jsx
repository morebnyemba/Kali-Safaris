import React from 'react';
import { Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart } from 'recharts';
import { FiLoader, FiBarChart2 } from 'react-icons/fi';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="p-2 bg-background border rounded-md shadow-lg text-sm">
        <p className="font-bold mb-1">{label}</p>
        <p className="text-purple-500">{`Incoming: ${payload[0].value}`}</p>
        <p className="text-teal-500">{`Outgoing: ${payload[1].value}`}</p>
      </div>
    );
  }
  return null;
};

export default function MessageVolumeChart({ data, isLoading }) {
  if (isLoading) return <div className="flex items-center justify-center h-full"><FiLoader className="animate-spin h-8 w-8 text-muted-foreground" /></div>;
  if (!data || data.length === 0) return <div className="flex items-center justify-center h-full text-muted-foreground"><FiBarChart2 className="mr-2" />No data for this period.</div>;

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis dataKey="period" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} tickLine={{ stroke: 'hsl(var(--muted-foreground))' }} />
        <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
        <Tooltip content={<CustomTooltip />} cursor={{fill: 'hsl(var(--muted))'}} />
        <Legend wrapperStyle={{ fontSize: '14px' }} />
        <Bar dataKey="incoming_messages" name="Incoming" stackId="a" fill="hsl(var(--primary))" />
        <Bar dataKey="outgoing_messages" name="Outgoing" stackId="a" fill="hsl(var(--secondary-foreground))" opacity={0.7} />
      </BarChart>
    </ResponsiveContainer>
  );
}