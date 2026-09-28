import React, { useState } from 'react';
import { toast } from 'sonner';
import { FileSpreadsheet, FileText, Loader2, Users, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toLocalIsoDate } from '@/lib/utils';
import { ordersApi } from '@/services/orders';

const addDays = (days) => {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return toLocalIsoDate(d);
};

const MANIFESTS = [
  {
    kind: 'park',
    title: 'Park entry manifest',
    description: 'ZimParks format — one numbered row per passenger with ID, nationality and age.',
    icon: ShieldCheck,
  },
  {
    kind: 'summary',
    title: 'Passenger summary',
    description: 'Crew headcount per booking group for seating and park fees.',
    icon: Users,
  },
];

/**
 * Download park / summary manifests for a tour date. Only Paid and
 * Deposit Paid bookings are included (enforced server-side).
 */
export default function ManifestExportPanel({ date, onDateChange }) {
  const [busy, setBusy] = useState(null); // `${kind}:${format}` while downloading

  const quickDates = [
    { label: 'Today', value: addDays(0) },
    { label: 'Tomorrow', value: addDays(1) },
  ];

  const download = async (kind, format) => {
    if (!date) {
      toast.error('Pick a tour date first.');
      return;
    }
    setBusy(`${kind}:${format}`);
    try {
      await ordersApi.downloadManifest(kind, date, format);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>Passenger manifests</CardTitle>
        <CardDescription>
          Confirmed passengers (Paid / Deposit Paid) for a single tour date. Passengers still missing
          details are listed as “Details pending”.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-end gap-3">
          <div className="space-y-1">
            <Label htmlFor="manifest-date">Tour date</Label>
            <Input
              id="manifest-date"
              type="date"
              value={date}
              onChange={(e) => onDateChange(e.target.value)}
              className="w-44"
            />
          </div>
          {quickDates.map(({ label, value }) => (
            <Button
              key={label}
              type="button"
              size="sm"
              variant={date === value ? 'secondary' : 'outline'}
              onClick={() => onDateChange(value)}
            >
              {label}
            </Button>
          ))}
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          {MANIFESTS.map(({ kind, title, description, icon }) => {
            const Icon = icon;
            return (
            <div key={kind} className="rounded-lg border p-4 flex flex-col gap-3">
              <div className="flex items-start gap-3">
                <Icon className="size-5 mt-0.5 text-muted-foreground" aria-hidden />
                <div>
                  <p className="font-medium">{title}</p>
                  <p className="text-sm text-muted-foreground">{description}</p>
                </div>
              </div>
              <div className="flex gap-2">
                {[
                  { format: 'pdf', label: 'PDF', formatIcon: FileText },
                  { format: 'excel', label: 'Excel', formatIcon: FileSpreadsheet },
                ].map(({ format, label, formatIcon }) => {
                  const FormatIcon = formatIcon;
                  const isBusy = busy === `${kind}:${format}`;
                  return (
                    <Button
                      key={format}
                      type="button"
                      size="sm"
                      variant={format === 'pdf' ? 'default' : 'outline'}
                      disabled={Boolean(busy) || !date}
                      onClick={() => download(kind, format)}
                      aria-label={`Download ${title} as ${label}`}
                    >
                      {isBusy ? <Loader2 className="animate-spin" /> : <FormatIcon />}
                      {label}
                    </Button>
                  );
                })}
              </div>
            </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
