import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { apiCall } from '@/lib/api';

// UI Components
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { FiSave, FiLoader } from 'react-icons/fi';

const ministrySchema = z.object({
  name: z.string().min(3, "Ministry name is required."),
  description: z.string().optional(),
  leader_name: z.string().optional(),
  contact_info: z.string().optional(),
  meeting_schedule: z.string().optional(),
  is_active: z.boolean().default(true),
});

export default function MinistryFormPage() {
  const { ministryId } = useParams();
  const navigate = useNavigate();
  const isEditMode = Boolean(ministryId);

  const form = useForm({
    resolver: zodResolver(ministrySchema),
    defaultValues: {
      name: '',
      description: '',
      leader_name: '',
      contact_info: '',
      meeting_schedule: '',
      is_active: true,
    },
  });

  useEffect(() => {
    if (isEditMode) {
      const fetchMinistry = async () => {
        try {
          const data = await apiCall(`/crm-api/church-services/ministries/${ministryId}/`);
          form.reset(data);
        } catch (error) {
          toast.error("Failed to load ministry data.");
          navigate('/ministries');
        }
      };
      fetchMinistry();
    }
  }, [isEditMode, ministryId, form, navigate]);

  const onSubmit = async (data) => {
    try {
      const apiPromise = isEditMode
        ? apiCall(`/crm-api/church-services/ministries/${ministryId}/`, 'PUT', data)
        : apiCall('/crm-api/church-services/ministries/', 'POST', data);

      await toast.promise(apiPromise, {
        loading: 'Saving ministry...',
        success: `Ministry successfully ${isEditMode ? 'updated' : 'created'}!`,
        error: `Failed to save ministry.`,
      });
      navigate('/ministries');
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
              <CardTitle>{isEditMode ? 'Edit Ministry' : 'Create New Ministry'}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <FormField control={form.control} name="name" render={({ field }) => (<FormItem><FormLabel>Ministry Name</FormLabel><FormControl><Input placeholder="e.g., Youth Ministry" {...field} /></FormControl><FormMessage /></FormItem>)} />
              <FormField control={form.control} name="leader_name" render={({ field }) => (<FormItem><FormLabel>Leader's Name</FormLabel><FormControl><Input placeholder="John Doe" {...field} /></FormControl><FormMessage /></FormItem>)} />
              <FormField control={form.control} name="contact_info" render={({ field }) => (<FormItem><FormLabel>Contact Info</FormLabel><FormControl><Input placeholder="Phone or Email" {...field} /></FormControl><FormMessage /></FormItem>)} />
              <FormField control={form.control} name="meeting_schedule" render={({ field }) => (<FormItem><FormLabel>Meeting Schedule</FormLabel><FormControl><Input placeholder="e.g., Tuesdays at 7 PM" {...field} /></FormControl><FormMessage /></FormItem>)} />
              <FormField control={form.control} name="description" render={({ field }) => (<FormItem><FormLabel>Description</FormLabel><FormControl><Textarea placeholder="Details about the ministry..." {...field} /></FormControl><FormMessage /></FormItem>)} />
              <FormField control={form.control} name="is_active" render={({ field }) => (
                  <FormItem className="flex flex-row items-center space-x-2">
                    <FormControl><Checkbox checked={field.value} onCheckedChange={field.onChange} /></FormControl>
                    <FormLabel>Ministry is Active</FormLabel>
                  </FormItem>
                )}
              />
            </CardContent>
            <CardFooter className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => navigate('/ministries')}>Cancel</Button>
              <Button type="submit" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting ? <FiLoader className="animate-spin mr-2" /> : <FiSave className="mr-2" />}
                {isEditMode ? 'Save Changes' : 'Create Ministry'}
              </Button>
            </CardFooter>
          </Card>
        </form>
      </Form>
    </div>
  );
}