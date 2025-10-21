
import React, { useEffect, useState } from 'react';
import { analyticsApi } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { DatePickerWithRange } from '@/components/ui/date-range-picker';
import { FiLoader, FiDownload, FiFilter, FiFileText } from 'react-icons/fi';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table.jsx';


export default function ReportsPage() {
  const [reports, setReports] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState({
    from: new Date(new Date().setDate(new Date().getDate() - 30)),
    to: new Date(),
  });
  const [selectedType, setSelectedType] = useState('all');
  const [search, setSearch] = useState('');

  const fetchReports = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = {
        start_date: dateRange.from.toISOString().slice(0, 10),
        end_date: dateRange.to.toISOString().slice(0, 10),
        type: selectedType !== 'all' ? selectedType : undefined,
        search: search || undefined,
      };
      const res = await analyticsApi.getReports(params);
      setReports(res.data.reports || []);
    } catch (err) {
      setError(err.message || 'Failed to fetch reports');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
    // eslint-disable-next-line
  }, [dateRange, selectedType]);

  const handleExport = (report, format = 'csv') => {
    // Example: CSV export for tabular data
    if (report.data && Array.isArray(report.data)) {
      if (format === 'csv') {
        const csv = [Object.keys(report.data[0]).join(',')]
          .concat(report.data.map(row => Object.values(row).join(',')))
          .join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${report.title.replace(/\s+/g, '_').toLowerCase()}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      } else if (format === 'pdf') {
        alert('PDF export coming soon!');
      }
    } else {
      alert('No tabular data to export.');
    }
  };

  // Example: get all unique report types for filter dropdown
  const reportTypes = ['all', ...Array.from(new Set(reports.map(r => r.type).filter(Boolean)))];

  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8 space-y-8">
      <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <h1 className="text-2xl font-bold">Reports</h1>
        <div className="flex flex-wrap items-center gap-2">
          <DatePickerWithRange date={dateRange} onDateChange={setDateRange} />
          <select
            className="border rounded px-2 py-1 text-sm"
            value={selectedType}
            onChange={e => setSelectedType(e.target.value)}
          >
            {reportTypes.map(type => (
              <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
            ))}
          </select>
          <input
            type="text"
            className="border rounded px-2 py-1 text-sm"
            placeholder="Search reports..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && fetchReports()}
          />
          <Button onClick={fetchReports} disabled={isLoading}>
            <FiFilter className="mr-1" /> Filter
          </Button>
        </div>
      </div>
      {isLoading && <div className="text-center p-8"><FiLoader className="animate-spin h-8 w-8 mx-auto text-slate-500" /></div>}
      {error && <p className="text-red-500 text-center p-8">{error}</p>}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {reports.length === 0 && !isLoading && !error && (
          <Card>
            <CardHeader>
              <CardTitle>No reports found for this period.</CardTitle>
            </CardHeader>
          </Card>
        )}
        {reports.map((report) => (
          <Card key={report.id} className="col-span-1">
            <CardHeader className="flex flex-row items-center gap-2">
              <FiFileText className="text-blue-500 text-lg" />
              <CardTitle>{report.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="mb-2 text-slate-600">{report.description}</p>
              {report.data && Array.isArray(report.data) && report.data.length > 0 && (
                <div className="mb-4 overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {Object.keys(report.data[0]).map((k) => (
                          <TableHead key={k}>{k.replace(/_/g, ' ').toUpperCase()}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {report.data.map((row, i) => (
                        <TableRow key={i}>
                          {Object.keys(report.data[0]).map((k) => (
                            <TableCell key={k}>{row[k]}</TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => handleExport(report, 'csv')}>
                  <FiDownload className="mr-2" /> Export CSV
                </Button>
                <Button variant="outline" onClick={() => handleExport(report, 'pdf')}>
                  <FiDownload className="mr-2" /> Export PDF
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
