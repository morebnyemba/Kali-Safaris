import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDebounce } from 'use-debounce';
import { toast } from 'sonner';
import { apiCall } from '@/lib/api';

// UI Components
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { FiSearch, FiVideo, FiMic, FiUser, FiCalendar, FiPlus, FiEdit, FiTrash2 } from 'react-icons/fi';

const SermonCard = ({ sermon, onEdit, onDelete }) => {
  return (
    <Card className="flex flex-col h-full dark:bg-slate-800 transition-shadow hover:shadow-lg">
      <CardHeader>
        <CardTitle className="text-lg">{sermon.title}</CardTitle>
        <CardDescription>
          <div className="flex items-center text-sm text-muted-foreground mt-1">
            <FiUser className="mr-2 h-4 w-4 flex-shrink-0" />
            <span className="truncate" title={sermon.preacher}>{sermon.preacher}</span>
            <span className="mx-2">|</span>
            <FiCalendar className="mr-2 h-4 w-4 flex-shrink-0" />
            <span>{new Date(sermon.sermon_date).toLocaleDateString()}</span>
          </div>
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-grow">
        <p className="text-sm text-muted-foreground line-clamp-3">
          {sermon.description || 'No description available.'}
        </p>
      </CardContent>
      <CardFooter className="flex justify-between items-center pt-4">
        <div className="flex gap-2">
          {sermon.video_link && (
            <a href={sermon.video_link} target="_blank" rel="noopener noreferrer" title="Watch Video">
              <Button variant="outline" size="icon"><FiVideo className="h-4 w-4" /></Button>
            </a>
          )}
          {sermon.audio_link && (
            <a href={sermon.audio_link} target="_blank" rel="noopener noreferrer" title="Listen to Audio">
              <Button variant="outline" size="icon"><FiMic className="h-4 w-4" /></Button>
            </a>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="icon" onClick={() => onEdit(sermon.id)}><FiEdit className="h-4 w-4 text-muted-foreground" /></Button>
          <Button variant="ghost" size="icon" onClick={() => onDelete(sermon.id)}><FiTrash2 className="h-4 w-4 text-destructive" /></Button>
        </div>
      </CardFooter>
    </Card>
  );
};

export default function SermonsPage() {
  const [sermons, setSermons] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm] = useDebounce(searchTerm, 500);
  const navigate = useNavigate();

  const fetchSermons = useCallback(async (search = '') => {
    setIsLoading(true);
    try {
      const data = await apiCall(`/crm-api/church-services/sermons/?search=${encodeURIComponent(search)}`);
      setSermons(data.results || []);
    } catch (error) {
      toast.error("Failed to load sermons.");
      console.error("Error fetching sermons:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSermons(debouncedSearchTerm);
  }, [debouncedSearchTerm, fetchSermons]);

  const handleDelete = async (sermonId) => {
    if (!window.confirm("Are you sure you want to delete this sermon? This action cannot be undone.")) {
      return;
    }
    try {
      await apiCall(`/crm-api/church-services/sermons/${sermonId}/`, 'DELETE');
      toast.success("Sermon deleted successfully.");
      // Refresh the list after deletion
      setSermons(prev => prev.filter(s => s.id !== sermonId));
    } catch (error) {
      toast.error("Failed to delete sermon.");
    }
  };

  return (
    <div className="space-y-8 p-4 md:p-8">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold">Sermon Library</h1>
          <p className="text-muted-foreground">Browse and search for past sermons.</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative w-full sm:w-72">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input placeholder="Search by title, preacher..." className="pl-9" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
          </div>
          <Button onClick={() => navigate('/sermons/new')}>
            <FiPlus className="mr-2 h-4 w-4" /> Create Sermon
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          [...Array(6)].map((_, i) => (<Card key={i}><CardHeader><Skeleton className="h-6 w-3/4" /></CardHeader><CardContent className="space-y-2"><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-5/6" /></CardContent><CardFooter><Skeleton className="h-8 w-1/2" /></CardFooter></Card>))
        ) : sermons.length > 0 ? (
          sermons.map(sermon => <SermonCard key={sermon.id} sermon={sermon} onEdit={() => navigate(`/sermons/edit/${sermon.id}`)} onDelete={handleDelete} />)
        ) : (
          <div className="col-span-full text-center py-16"><h2 className="text-xl font-semibold">No Sermons Found</h2><p className="text-muted-foreground mt-2">{searchTerm ? "Try adjusting your search terms." : "There are no sermons in the library yet."}</p></div>
        )}
      </div>
    </div>
  );
}