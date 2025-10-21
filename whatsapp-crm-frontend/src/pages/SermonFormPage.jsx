import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { apiCall } from '@/lib/api';

// UI Components
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { FiSave, FiLoader } from 'react-icons/fi';

// Validation schema for the sermon form
const sermonSchema = z.object({
  title: z.string().min(3, "Title must be at least 3 characters."),
  preacher: z.string().min(3, "Preacher name is required."),
  sermon_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Please enter a valid date."),
  description: z.string().optional(),
  video_link: z.string().url("Please enter a valid URL.").optional().or(z.literal('')),
  audio_link: z.string().url("Please enter a valid URL.").optional().or(z.literal('')),
  is_published: z.boolean().default(false),
});

export default function SermonFormPage() {
  const { sermonId } = useParams();
  const navigate = useNavigate();
  const isEditMode = Boolean(sermonId);

  const form = useForm({
    resolver: zodResolver(sermonSchema),
    defaultValues: {
      title: '',
      preacher: '',
      sermon_date: '',
      description: '',
      video_link: '',
      audio_link: '',
      is_published: false,
    },
  });

  useEffect(() => {
    if (isEditMode) {
      const fetchSermon = async () => {
        try {
          const sermonData = await apiCall(`/crm-api/church-services/sermons/${sermonId}/`);
          // Populate form with fetched data
          form.reset({
            ...sermonData,
            sermon_date: sermonData.sermon_date || '', // Ensure date is a string
          });
        } catch (error) {
          toast.error("Failed to load sermon data for editing.");
          navigate('/sermons');
        }
      };
      fetchSermon();
    }
  }, [isEditMode, sermonId, form, navigate]);

  const onSubmit = async (data) => {
    try {
      const apiPromise = isEditMode
        ? apiCall(`/crm-api/church-services/sermons/${sermonId}/`, 'PUT', data)
        : apiCall('/crm-api/church-services/sermons/', 'POST', data);

      await toast.promise(apiPromise, {
        loading: 'Saving sermon...',
        success: `Sermon successfully ${isEditMode ? 'updated' : 'created'}!`,
        error: `Failed to ${isEditMode ? 'update' : 'create'} sermon.`,
      });

      navigate('/sermons');
    } catch (error) {
      // Error toast is already handled by toast.promise
      console.error("Submission error:", error);
    }
  };

  return (
    <div className="p-4 md:p-8">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <Card className="max-w-3xl mx-auto">
            <CardHeader>
              <CardTitle>{isEditMode ? 'Edit Sermon' : 'Create New Sermon'}</CardTitle>
              <CardDescription>
                {isEditMode ? 'Update the details of this sermon.' : 'Fill out the form to add a new sermon to the library.'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <FormField control={form.control} name="title" render={({ field }) => (<FormItem><FormLabel>Title</FormLabel><FormControl><Input placeholder="Sermon Title" {...field} /></FormControl><FormMessage /></FormItem>)} />
                <FormField control={form.control} name="preacher" render={({ field }) => (<FormItem><FormLabel>Preacher</FormLabel><FormControl><Input placeholder="e.g., Pastor John Doe" {...field} /></FormControl><FormMessage /></FormItem>)} />
              </div>
              <FormField control={form.control} name="sermon_date" render={({ field }) => (<FormItem><FormLabel>Sermon Date</FormLabel><FormControl><Input type="date" {...field} /></FormControl><FormMessage /></FormItem>)} />
              <FormField control={form.control} name="description" render={({ field }) => (<FormItem><FormLabel>Description</FormLabel><FormControl><Textarea placeholder="A brief summary of the sermon..." {...field} /></FormControl><FormMessage /></FormItem>)} />
              <FormField control={form.control} name="video_link" render={({ field }) => (<FormItem><FormLabel>Video Link (YouTube, etc.)</FormLabel><FormControl><Input type="url" placeholder="https://..." {...field} /></FormControl><FormMessage /></FormItem>)} />
              <FormField control={form.control} name="audio_link" render={({ field }) => (<FormItem><FormLabel>Audio Link (SoundCloud, etc.)</FormLabel><FormControl><Input type="url" placeholder="https://..." {...field} /></FormControl><FormMessage /></FormItem>)} />
              <FormField
                control={form.control}
                name="is_published"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4 shadow">
                    <FormControl>
                      <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <FormLabel>Publish Sermon</FormLabel>
                      <CardDescription>Make this sermon visible to all users on the sermons page.</CardDescription>
                    </div>
                  </FormItem>
                )}
              />
            </CardContent>
            <CardFooter className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => navigate('/sermons')}>Cancel</Button>
              <Button type="submit" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting ? <FiLoader className="animate-spin mr-2" /> : <FiSave className="mr-2" />}
                {isEditMode ? 'Save Changes' : 'Create Sermon'}
              </Button>
            </CardFooter>
          </Card>
        </form>
      </Form>
    </div>
  );
}