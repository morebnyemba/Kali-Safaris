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
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-green-400 via-teal-500 to-blue-600 dark:from-gray-800 dark:via-gray-900 dark:to-black p-4">
      <Card className="w-full max-w-md shadow-2xl dark:bg-gray-800">
        <CardHeader className="text-center">
          {/* Logo removed as requested */}
          <CardTitle className="text-3xl font-bold text-gray-800 dark:text-gray-100">Welcome Back!</CardTitle>
          <CardDescription className="text-gray-600 dark:text-gray-400">
            Log in to your WhatsApp CRM dashboard.
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
                    <FormLabel className="text-gray-700 dark:text-gray-300">Username</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Enter your username"
                        {...field}
                        disabled={form.formState.isSubmitting}
                        className="dark:bg-gray-700 dark:border-gray-600 dark:text-gray-50"
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
                    <FormLabel className="text-gray-700 dark:text-gray-300">Password</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Input
                          type={showPassword ? "text" : "password"}
                          placeholder="Enter your password"
                          {...field}
                          disabled={form.formState.isSubmitting}
                          className="dark:bg-gray-700 dark:border-gray-600 dark:text-gray-50 pr-10"
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
              <Button type="submit" className="w-full bg-green-600 hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600 text-white" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting && <FiLoader className="animate-spin mr-2" />}
                {form.formState.isSubmitting ? 'Logging in...' : 'Log In'}
              </Button>
            </form>
          </Form>
        </CardContent>
        <CardFooter className="flex flex-col items-center text-xs text-gray-500 dark:text-gray-400 pt-4">
          <p>&copy; {new Date().getFullYear()} AutoWhatsapp CRM</p>
        </CardFooter>
      </Card>
    </div>
  );
}
