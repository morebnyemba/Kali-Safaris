import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { apiCall } from '@/lib/api';
import { format } from 'date-fns';

// UI Components
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { FiSave, FiLoader } from 'react-icons/fi';

const eventSchema = z.object({
  title: z.string().min(3, "Title is required."),
  description: z.string().optional(),
  start_time: z.string().min(1, "Start date and time are required."),
  end_time: z.string().optional(),
  location: z.string().optional(),
  is_active: z.boolean().default(true),
});

export default function EventFormPage() {
  const { eventId } = useParams();
  const navigate = useNavigate();
  const isEditMode = Boolean(eventId);

  const form = useForm({
    resolver: zodResolver(eventSchema),
    defaultValues: {
      title: '',
      description: '',
      start_time: '',
      end_time: '',
      location: '',
      is_active: true,
    },
  });

  const formatDateForInput = (dateString) => {
    if (!dateString) return '';
    // The input type="datetime-local" expects "YYYY-MM-DDTHH:mm"
    return format(new Date(dateString), "yyyy-MM-dd'T'HH:mm");
  };

  useEffect(() => {
    if (isEditMode) {
      const fetchEvent = async () => {
        try {
          const data = await apiCall(`/crm-api/church-services/events/${eventId}/`);
          form.reset({
            ...data,
            start_time: formatDateForInput(data.start_time),
            end_time: formatDateForInput(data.end_time),
          });
        } catch (error) {
          toast.error("Failed to load event data.");
          navigate('/events');
        }
      };
      fetchEvent();
    }
  }, [isEditMode, eventId, form, navigate]);

  const onSubmit = async (data) => {
    const payload = {
      ...data,
      start_time: new Date(data.start_time).toISOString(),
      end_time: data.end_time ? new Date(data.end_time).toISOString() : null,
    };

    try {
      const apiPromise = isEditMode
        ? apiCall(`/crm-api/church-services/events/${eventId}/`, 'PUT', payload)
        : apiCall('/crm-api/church-services/events/', 'POST', payload);

      await toast.promise(apiPromise, {
        loading: 'Saving event...',
        success: `Event successfully ${isEditMode ? 'updated' : 'created'}!`,
        error: `Failed to save event.`,
      });
      navigate('/events');
    } catch (error) {
      console.error("Submission error:", error);
    }
  };

  return (
    <div className="p-4 md:p-8">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <Card className="max-w-3xl mx-auto">
            <CardHeader>
              <CardTitle>{isEditMode ? 'Edit Event' : 'Create New Event'}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <FormField control={form.control} name="title" render={({ field }) => (<FormItem><FormLabel>Title</FormLabel><FormControl><Input placeholder="Event Title" {...field} /></FormControl><FormMessage /></FormItem>)} />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <FormField control={form.control} name="start_time" render={({ field }) => (<FormItem><FormLabel>Start Time</FormLabel><FormControl><Input type="datetime-local" {...field} /></FormControl><FormMessage /></FormItem>)} />
                <FormField control={form.control} name="end_time" render={({ field }) => (<FormItem><FormLabel>End Time (Optional)</FormLabel><FormControl><Input type="datetime-local" {...field} /></FormControl><FormMessage /></FormItem>)} />
              </div>
              <FormField control={form.control} name="location" render={({ field }) => (<FormItem><FormLabel>Location</FormLabel><FormControl><Input placeholder="e.g., Main Hall" {...field} /></FormControl><FormMessage /></FormItem>)} />
              <FormField control={form.control} name="description" render={({ field }) => (<FormItem><FormLabel>Description</FormLabel><FormControl><Textarea placeholder="Details about the event..." {...field} /></FormControl><FormMessage /></FormItem>)} />
              <FormField control={form.control} name="is_active" render={({ field }) => (
                  <FormItem className="flex flex-row items-center space-x-2">
                    <FormControl><Checkbox checked={field.value} onCheckedChange={field.onChange} /></FormControl>
                    <FormLabel>Event is Active</FormLabel>
                  </FormItem>
                )}
              />
            </CardContent>
            <CardFooter className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => navigate('/events')}>Cancel</Button>
              <Button type="submit" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting ? (
                  <FiLoader className="animate-spin mr-2" />
                ) : (
                  <FiSave className="mr-2" />
                )}
                {isEditMode ? 'Save Changes' : 'Create Event'}
              </Button>
            </CardFooter>
          </Card>
        </form>
      </Form>
    </div>
  );
}