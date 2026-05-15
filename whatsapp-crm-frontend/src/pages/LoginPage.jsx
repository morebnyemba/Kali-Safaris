// Filename: src/pages/LoginPage.jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { toast } from 'sonner';
import { FiEye, FiEyeOff, FiLoader, FiAlertCircle } from 'react-icons/fi';
import { BRAND_ATTRIBUTION } from '@/config/appConfig';

const loginSchema = z.object({
  username: z.string().min(1, { message: "Username is required." }),
  password: z.string().min(1, { message: "Password is required." }),
});

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || "/dashboard"; // Redirect to intended page or dashboard

  const form = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' },
  });

  const onSubmit = async (data) => {
    const result = await login(data.username, data.password);

    if (result.success) {
      toast.success("Login successful! Redirecting...");
      navigate(from, { replace: true });
    } else {
      form.setError("root", {
        type: "manual",
        message: result.error || "An unexpected error occurred.",
      });
      form.setFocus("username");
    }
  };

  useEffect(() => {
    form.setFocus("username");
  }, [form]);

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-linear-to-br from-cyan-200 via-sky-300 to-indigo-300 p-4 dark:from-slate-950 dark:via-slate-900 dark:to-slate-800">
      <div className="pointer-events-none absolute -left-20 top-16 h-72 w-72 rounded-full bg-cyan-400/30 blur-3xl" />
      <div className="pointer-events-none absolute -right-24 bottom-8 h-80 w-80 rounded-full bg-indigo-400/30 blur-3xl" />

      <Card className="w-full max-w-md border-slate-200/70 bg-white/90 shadow-2xl backdrop-blur-sm dark:border-slate-700 dark:bg-slate-900/85">
        <CardHeader className="text-center">
          <CardTitle className="text-3xl font-bold text-slate-900 dark:text-slate-100">Kalai Safaris CRM</CardTitle>
          <CardDescription className="text-slate-600 dark:text-slate-300">
            Secure sign-in for operations, analytics, and admin controls.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              {form.formState.errors.root && (
                <div className="flex items-center gap-x-2 text-sm text-red-500 dark:text-red-400 bg-red-100 dark:bg-red-900/30 p-3 rounded-md">
                  <FiAlertCircle className="h-4 w-4" aria-hidden="true" />
                  <p>{form.formState.errors.root.message}</p>
                </div>
              )}
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-slate-700 dark:text-slate-300">Username</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Enter your username"
                        {...field}
                        disabled={form.formState.isSubmitting}
                        className="dark:bg-slate-800 dark:border-slate-700 dark:text-slate-50"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-slate-700 dark:text-slate-300">Password</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Input
                          type={showPassword ? "text" : "password"}
                          placeholder="Enter your password"
                          {...field}
                          disabled={form.formState.isSubmitting}
                          className="pr-10 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-50"
                        />
                        <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200" aria-label={showPassword ? "Hide password" : "Show password"}>
                          {showPassword ? <FiEyeOff /> : <FiEye />}
                        </button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button type="submit" className="w-full bg-cyan-600 text-white hover:bg-cyan-700 dark:bg-cyan-500 dark:hover:bg-cyan-600" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting && <FiLoader className="animate-spin mr-2" />}
                {form.formState.isSubmitting ? 'Logging in...' : 'Log In'}
              </Button>
            </form>
          </Form>
        </CardContent>
        <CardFooter className="flex flex-col items-center gap-1 pt-4 text-xs text-slate-500 dark:text-slate-400">
          <p>&copy; {new Date().getFullYear()} Kalai Safaris CRM</p>
          <a href={BRAND_ATTRIBUTION.url} target="_blank" rel="noopener noreferrer" className="font-medium text-cyan-700 hover:underline dark:text-cyan-400">
            {BRAND_ATTRIBUTION.text}
          </a>
        </CardFooter>
      </Card>
    </div>
  );
}
