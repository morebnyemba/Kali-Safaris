import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { apiCall } from '@/lib/api';

// UI Components
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { FiUsers, FiUser, FiClock, FiPlus, FiEdit, FiTrash2 } from 'react-icons/fi';

const MinistryCard = ({ ministry, onEdit, onDelete }) => {
  return (
    <Card className="flex flex-col h-full dark:bg-slate-800 transition-shadow hover:shadow-lg">
      <CardHeader>
        <CardTitle className="text-lg">{ministry.name}</CardTitle>
        {ministry.leader_name && (
          <CardDescription>
            <div className="flex items-center text-sm text-muted-foreground mt-1">
              <FiUser className="mr-2 h-4 w-4 flex-shrink-0" />
              <span>Led by: {ministry.leader_name}</span>
            </div>
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-grow">
        <p className="text-sm text-muted-foreground line-clamp-3">
          {ministry.description || 'No description available.'}
        </p>
        {ministry.meeting_schedule && (
          <div className="flex items-center text-sm text-muted-foreground mt-4">
            <FiClock className="mr-2 h-4 w-4 flex-shrink-0" />
            <span>{ministry.meeting_schedule}</span>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-end pt-4">
        <div className="flex gap-2">
          <Button variant="ghost" size="icon" onClick={() => onEdit(ministry.id)}><FiEdit className="h-4 w-4 text-muted-foreground" /></Button>
          <Button variant="ghost" size="icon" onClick={() => onDelete(ministry.id)}><FiTrash2 className="h-4 w-4 text-destructive" /></Button>
        </div>
      </CardFooter>
    </Card>
  );
};

export default function MinistriesPage() {
  const [ministries, setMinistries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  const fetchMinistries = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await apiCall(`/crm-api/church-services/ministries/`);
      setMinistries(data.results || []);
    } catch (error) {
      toast.error("Failed to load ministries.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMinistries();
  }, [fetchMinistries]);

  const handleDelete = async (ministryId) => {
    if (!window.confirm("Are you sure you want to delete this ministry?")) return;
    try {
      await apiCall(`/crm-api/church-services/ministries/${ministryId}/`, 'DELETE');
      toast.success("Ministry deleted successfully.");
      setMinistries(prev => prev.filter(m => m.id !== ministryId));
    } catch (error) {
      toast.error("Failed to delete ministry.");
    }
  };

  return (
    <div className="space-y-8 p-4 md:p-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Our Ministries</h1>
          <p className="text-muted-foreground">Manage your church's ministries.</p>
        </div>
        <Button onClick={() => navigate('/ministries/new')}><FiPlus className="mr-2 h-4 w-4" /> Create Ministry</Button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading 
          ? ([...Array(3)].map((_, i) => <Card key={i}><CardHeader><Skeleton className="h-6 w-3/4" /></CardHeader><CardContent><Skeleton className="h-4 w-full" /></CardContent></Card>)) 
          : ministries.length > 0 
            ? (ministries.map(ministry => <MinistryCard key={ministry.id} ministry={ministry} onEdit={() => navigate(`/ministries/edit/${ministry.id}`)} onDelete={handleDelete} />)) 
            : (<p className="col-span-full text-center">No ministries found.</p>)}
      </div>
    </div>
  );
}