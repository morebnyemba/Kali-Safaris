import React from 'react';
import { Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, PieChart, Pie, Cell, Legend } from 'recharts';
import { FiLoader, FiBarChart2 } from 'react-icons/fi';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    // For Pie chart
    if (payload[0].name) {
        return (
            <div className="p-2 bg-background border rounded-md shadow-lg text-sm">
                <p>{`${payload[0].name}: ${payload[0].value}`}</p>
            </div>
        );
    }
    // For Bar chart
    return (
      <div className="p-2 bg-background border rounded-md shadow-lg text-sm">
        <p className="font-bold mb-1">{label}</p>
        <p className="text-red-500">{`Requests: ${payload[0].value}`}</p>
      </div>
    );
  }
  return null;
};

const RADIAN = Math.PI / 180;
const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central">
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

export default function PrayerRequestChart({ data, isLoading, groupBy }) {
  if (isLoading) return <div className="flex items-center justify-center h-full"><FiLoader className="animate-spin h-8 w-8 text-muted-foreground" /></div>;
  if (!data || data.length === 0) return <div className="flex items-center justify-center h-full text-muted-foreground"><FiBarChart2 className="mr-2" />No data for this period.</div>;

  if (groupBy === 'category') {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} cx="50%" cy="50%" labelLine={false} label={renderCustomizedLabel} outerRadius={80} fill="#8884d8" dataKey="requests" nameKey="category">
            {data.map((entry, index) => (<Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis dataKey="period" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} tickLine={{ stroke: 'hsl(var(--muted-foreground))' }} />
        <YAxis allowDecimals={false} stroke="hsl(var(--muted-foreground))" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
        <Tooltip content={<CustomTooltip />} cursor={{fill: 'hsl(var(--muted))'}} />
        <Bar dataKey="requests" name="Requests" fill="hsl(var(--primary))" opacity={0.7} />
      </BarChart>
    </ResponsiveContainer>
  );
}