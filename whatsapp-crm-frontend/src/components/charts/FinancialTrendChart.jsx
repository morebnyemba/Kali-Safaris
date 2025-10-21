import React from 'react';
import { Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart } from 'recharts';
import { FiLoader, FiBarChart2 } from 'react-icons/fi';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const totalAmount = payload.find(p => p.dataKey === 'total_amount');
    const transactions = payload.find(p => p.dataKey === 'transactions');
    return (
      <div className="p-2 bg-background border rounded-md shadow-lg text-sm">
        <p className="font-bold mb-1">{label}</p>
        {totalAmount && <p className="text-green-500">{`${totalAmount.name}: $${totalAmount.value.toLocaleString()}`}</p>}
        {transactions && <p className="text-blue-500">{`${transactions.name}: ${transactions.value}`}</p>}
      </div>
    );
  }
  return null;
};

export default function FinancialTrendChart({ data, isLoading }) {
  if (isLoading) return <div className="flex items-center justify-center h-full"><FiLoader className="animate-spin h-8 w-8 text-muted-foreground" /></div>;
  if (!data || data.length === 0) return <div className="flex items-center justify-center h-full text-muted-foreground"><FiBarChart2 className="mr-2" />No data for this period.</div>;

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis dataKey="period" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} tickLine={{ stroke: 'hsl(var(--muted-foreground))' }} />
        <YAxis yAxisId="left" orientation="left" stroke="hsl(var(--muted-foreground))" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} tickFormatter={(value) => `$${(value/1000)}k`} />
        <YAxis yAxisId="right" orientation="right" stroke="hsl(var(--muted-foreground))" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--muted))' }} />
        <Legend wrapperStyle={{ fontSize: '14px' }} />
        <Line yAxisId="left" type="monotone" dataKey="total_amount" name="Total Giving" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
        <Bar yAxisId="right" dataKey="transactions" name="Transactions" fill="hsl(var(--secondary-foreground))" opacity={0.6} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}