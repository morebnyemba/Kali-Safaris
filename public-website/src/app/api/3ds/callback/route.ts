import { type NextRequest, NextResponse } from 'next/server';

/**
 * Next.js route handler for 3DS v1 ACS callback.
 *
 * The ACS (bank's authentication server) does a form POST to this URL after
 * the cardholder completes the 3DS challenge. The POST body contains:
 *   - PaRes: Payment Authentication Response (base64-encoded XML from ACS)
 *   - MD:    Merchant Data — we set this to the merchant_reference
 *
 * We extract the merchant_reference and PaRes, then redirect the browser to
 * the payment-status page (GET), carrying the data as query params so the
 * page can forward PaRes to the Django backend for 3DS completion.
 */
export async function POST(request: NextRequest) {
  let paRes = '';
  let md = '';

  const contentType = request.headers.get('content-type') ?? '';

  if (contentType.includes('application/x-www-form-urlencoded') || contentType.includes('multipart/form-data')) {
    try {
      const formData = await request.formData();
      paRes = (formData.get('PaRes') as string) ?? (formData.get('pares') as string) ?? '';
      md = (formData.get('MD') as string) ?? (formData.get('md') as string) ?? '';
    } catch {
      // Fall through with empty values
    }
  } else {
    try {
      const text = await request.text();
      const params = new URLSearchParams(text);
      paRes = params.get('PaRes') ?? params.get('pares') ?? '';
      md = params.get('MD') ?? params.get('md') ?? '';
    } catch {
      // Fall through with empty values
    }
  }

  // MD is the merchant_reference we set when building the 3DS form
  const merchantReference = md.trim();

  // Build redirect URL for the payment-status page
  const redirectUrl = new URL('/booking/payment-status', request.url);
  redirectUrl.searchParams.set('channel', 'card');
  if (merchantReference) {
    redirectUrl.searchParams.set('ref', merchantReference);
  }
  if (paRes) {
    // Encode PaRes so it survives as a query param (it's already base64 but may contain +/=)
    redirectUrl.searchParams.set('pares', paRes);
  }

  return NextResponse.redirect(redirectUrl, { status: 303 });
}

// Some ACS implementations do a GET redirect instead of POST.
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const paRes = searchParams.get('PaRes') ?? searchParams.get('pares') ?? '';
  const md = searchParams.get('MD') ?? searchParams.get('md') ?? '';

  const redirectUrl = new URL('/booking/payment-status', request.url);
  redirectUrl.searchParams.set('channel', 'card');
  if (md) {
    redirectUrl.searchParams.set('ref', md.trim());
  }
  if (paRes) {
    redirectUrl.searchParams.set('pares', paRes);
  }

  return NextResponse.redirect(redirectUrl, { status: 303 });
}
