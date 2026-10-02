// Filename: src/pages/LoginPage.jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navigate, useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { FiEye, FiEyeOff, FiLoader, FiAlertCircle } from 'react-icons/fi';
import { BRAND_ATTRIBUTION } from '@/config/appConfig';

const loginSchema = z.object({
  username: z.string().min(1, { message: "Username is required." }),
  password: z.string().min(1, { message: "Password is required." }),
});

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const { login, isAuthenticated, isLoading } = useAuth();
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

  if (!isLoading && isAuthenticated) return <Navigate to={from} replace />;

  return (
    <div className="grid min-h-screen bg-background lg:grid-cols-[1fr_minmax(28rem,36rem)]">
      <aside className="relative hidden overflow-hidden bg-sidebar p-12 text-sidebar-foreground lg:flex lg:flex-col lg:justify-between">
        <div className="pointer-events-none absolute -right-32 -top-32 size-96 rounded-full bg-brand-accent/20 blur-3xl" aria-hidden />
        <div className="pointer-events-none absolute -bottom-40 -left-20 size-[28rem] rounded-full bg-primary/40 blur-3xl" aria-hidden />
        <div className="relative flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-lg bg-brand-accent text-lg font-bold text-white">K</span>
          <span className="text-lg font-semibold">Kalai Safaris</span>
        </div>
        <div className="relative max-w-md">
          <h2 className="text-3xl font-semibold leading-tight">Every booking, conversation and departure in one place.</h2>
          <p className="mt-4 text-sidebar-foreground/70">Answer WhatsApp customers, confirm passengers and print park manifests without leaving the console.</p>
        </div>
        <a href={BRAND_ATTRIBUTION.url} target="_blank" rel="noopener noreferrer" className="relative text-xs text-sidebar-foreground/60 hover:text-sidebar-foreground">
          {BRAND_ATTRIBUTION.text}
        </a>
      </aside>

      <main className="flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <span className="flex size-10 items-center justify-center rounded-lg bg-brand-accent text-lg font-bold text-white">K</span>
            <span className="text-lg font-semibold">Kalai Safaris</span>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">Sign in</h1>
          <p className="mt-1 text-sm text-muted-foreground">Use the account your administrator gave you.</p>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="mt-8 space-y-5" noValidate>
              {form.formState.errors.root && (
                <div role="alert" className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                  <FiAlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden />
                  <p>{form.formState.errors.root.message}</p>
                </div>
              )}
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Username</FormLabel>
                    <FormControl>
                      <Input autoComplete="username" autoCapitalize="none" {...field} disabled={form.formState.isSubmitting} />
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
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Input type={showPassword ? 'text' : 'password'} autoComplete="current-password" {...field} disabled={form.formState.isSubmitting} className="pr-10" />
                        <button type="button" onClick={() => setShowPassword((v) => !v)} className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-muted-foreground hover:text-foreground" aria-label={showPassword ? 'Hide password' : 'Show password'}>
                          {showPassword ? <FiEyeOff className="size-4" /> : <FiEye className="size-4" />}
                        </button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button type="submit" className="w-full" size="lg" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting && <FiLoader className="animate-spin" />}
                {form.formState.isSubmitting ? 'Signing in…' : 'Sign in'}
              </Button>
            </form>
          </Form>
          <p className="mt-10 text-center text-xs text-muted-foreground lg:hidden">
            © {new Date().getFullYear()} Kalai Safaris · <a href={BRAND_ATTRIBUTION.url} target="_blank" rel="noopener noreferrer" className="hover:underline">{BRAND_ATTRIBUTION.text}</a>
          </p>
        </div>
      </main>
    </div>
  );
}
