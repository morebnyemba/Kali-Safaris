import { NextRequest, NextResponse } from 'next/server';

const BACKEND_TARGET = (
  process.env.BACKEND_API_PROXY_TARGET ||
  process.env.NEXT_PUBLIC_BACKEND_API_BASE ||
  'http://localhost:8000'
).replace(/\/$/, '');

function buildTargetUrl(pathSegments: string[], request: NextRequest): string {
  let path = pathSegments.join('/');
  // Django routes in this project use trailing slashes; avoid POST 301 redirects.
  if (path && !path.endsWith('/')) {
    path = `${path}/`;
  }
  const query = request.nextUrl.search;
  return `${BACKEND_TARGET}/crm-api/${path}${query}`;
}

function forwardHeaders(request: NextRequest): Headers {
  const headers = new Headers(request.headers);
  // Set host to match the backend domain so Django's ALLOWED_HOSTS check passes.
  const backendHost = new URL(BACKEND_TARGET).host;
  headers.set('host', backendHost);
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
