// pages/SavedData.jsx
import { useEffect, useState, useCallback } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { savedDataApi } from '@/lib/api'; // Import our new API service
import { format, parseISO, isValid } from 'date-fns';

const DataSkeleton = () => (
  <div className="space-y-4">
    <Skeleton className="h-8 w-full" />
    <Skeleton className="h-8 w-full" />
    <Skeleton className="h-8 w-full" />
  </div>
)

export default function SavedData() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await savedDataApi.list();
      setData(response.data.results || response.data || []);
    } catch (error) {
      // Error is toasted by the interceptor
      setData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Saved Data</h1>
      {loading ? (
        <DataSkeleton />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Client</TableHead>
              <TableHead>Last Message</TableHead>
              <TableHead>Timestamp</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((item) => (
              <TableRow key={item.id}>
                <TableCell>{item.client}</TableCell>
                <TableCell>{item.lastMessage}</TableCell>
                <TableCell>
                  {item.timestamp && isValid(parseISO(item.timestamp))
                    ? format(parseISO(item.timestamp), 'PPp')
                    : 'N/A'
                  }
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}