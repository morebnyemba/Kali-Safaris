import { NextRequest, NextResponse } from 'next/server';

const BACKEND_TARGET = (
  process.env.BACKEND_API_PROXY_TARGET ||
  process.env.NEXT_PUBLIC_BACKEND_API_BASE ||
  'http://localhost:8000'
).replace(/\/$/, '');

function buildTargetUrl(pathSegments: string[], request: NextRequest): string {
  const path = pathSegments.join('/');
  const query = request.nextUrl.search;
  return `${BACKEND_TARGET}/crm-api/${path}${query}`;
}

function forwardHeaders(request: NextRequest): Headers {
  const headers = new Headers(request.headers);
  const incomingHost = request.headers.get('x-forwarded-host') || request.headers.get('host');
  if (incomingHost) {
    headers.set('host', incomingHost);
  }
  return headers;
}

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }): Promise<NextResponse> {
  const { path } = await context.params;
  const targetUrl = buildTargetUrl(path || [], request);

  const hasBody = request.method !== 'GET' && request.method !== 'HEAD';
  const response = await fetch(targetUrl, {
    method: request.method,
    headers: forwardHeaders(request),
    body: hasBody ? request.body : undefined,
    duplex: hasBody ? 'half' : undefined,
    cache: 'no-store',
  } as RequestInit & { duplex?: 'half' });

  return new NextResponse(response.body, {
    status: response.status,
    headers: response.headers,
  });
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context);
}

export async function PUT(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context);
}

export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context);
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context);
}

export async function OPTIONS(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context);
}
