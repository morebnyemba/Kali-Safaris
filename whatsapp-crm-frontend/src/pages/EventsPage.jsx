import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { apiCall } from '@/lib/api';
import { format } from 'date-fns';

// UI Components
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  FiCalendar, 
  FiMapPin, 
  FiPlus, 
  FiEdit, 
  FiTrash2, 
  FiLoader 
} from 'react-icons/fi';

const EventCard = ({ event, onEdit, onDelete, isDeleting }) => {
  const eventDate = event.start_time ? new Date(event.start_time) : null;
  const formattedDate = eventDate ? format(eventDate, 'PPP') : 'Date not set';
  const formattedTime = eventDate ? format(eventDate, 'p') : '';

  return (
    <Card className="flex flex-col h-full dark:bg-slate-800 transition-shadow hover:shadow-lg overflow-hidden">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg line-clamp-1">{event.title || 'Untitled Event'}</CardTitle>
        <CardDescription className="mt-2">
          <div className="flex items-center text-sm text-muted-foreground">
            <FiCalendar className="mr-2 h-4 w-4 flex-shrink-0" />
            <span>{formattedDate} at {formattedTime}</span>
          </div>
          {event.location && (
            <div className="flex items-center text-sm text-muted-foreground mt-2">
              <FiMapPin className="mr-2 h-4 w-4 flex-shrink-0" />
              <span className="line-clamp-1">{event.location}</span>
            </div>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-grow pb-3">
        <p className="text-sm text-muted-foreground line-clamp-3">
          {event.description || 'No description available.'}
        </p>
      </CardContent>
      <CardFooter className="flex justify-end p-4 border-t">
        <div className="flex gap-2">
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={() => onEdit(event.id)}
            aria-label={`Edit ${event.title}`}
          >
            <FiEdit className="h-4 w-4 text-muted-foreground" />
          </Button>
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={() => onDelete(event.id)}
            disabled={isDeleting}
            aria-label={`Delete ${event.title}`}
          >
            {isDeleting ? (
              <FiLoader className="h-4 w-4 text-destructive animate-spin" />
            ) : (
              <FiTrash2 className="h-4 w-4 text-destructive" />
            )}
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
};

export default function EventsPage() {
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const navigate = useNavigate();

  const fetchEvents = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await apiCall(`/crm-api/church-services/events/`);
      setEvents(data.results || []);
    } catch (error) {
      toast.error("Failed to load events. Please try again later.");
      console.error('Events fetch error:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const handleDelete = async (eventId) => {
    if (!window.confirm("Are you sure you want to permanently delete this event?")) return;
    
    try {
      setIsDeleting(true);
      setDeletingId(eventId);
      await apiCall(`/crm-api/church-services/events/${eventId}/`, 'DELETE');
      toast.success("Event deleted successfully.");
      setEvents(prev => prev.filter(e => e.id !== eventId));
    } catch (error) {
      toast.error("Failed to delete event. Please check your connection.");
      console.error('Delete error:', error);
    } finally {
      setIsDeleting(false);
      setDeletingId(null);
    }
  };

  // Mobile-first responsive grid
  return (
    <div className="space-y-6 p-4 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold">Upcoming Events</h1>
          <p className="text-muted-foreground mt-1">Manage your church's events</p>
        </div>
        <Button 
          onClick={() => navigate('/events/new')} 
          className="w-full sm:w-auto"
        >
          <FiPlus className="mr-2 h-4 w-4" /> 
          <span>Create Event</span>
        </Button>
      </div>

      {/* Responsive grid with skeleton loading */}
      <div className="grid grid-cols-1 min-[500px]:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="h-56">
              <CardHeader>
                <Skeleton className="h-6 w-3/4 mb-2" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-4/5 mt-2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-full mt-2" />
                <Skeleton className="h-4 w-5/6 mt-2" />
              </CardContent>
            </Card>
          ))
        ) : events.length > 0 ? (
          events.map(event => (
            <EventCard 
              key={event.id}
              event={event}
              onEdit={() => navigate(`/events/edit/${event.id}`)}
              onDelete={handleDelete}
              isDeleting={isDeleting && deletingId === event.id}
            />
          ))
        ) : (
          <div className="col-span-full text-center py-12">
            <div className="text-muted-foreground mb-4">No upcoming events found</div>
            <Button onClick={() => navigate('/events/new')}>
              Create Your First Event
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}