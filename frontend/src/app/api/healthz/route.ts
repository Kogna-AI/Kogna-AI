export async function GET() {
  // Use the standard Next.js Response object to return a 200 status.
  // This is the fastest way to confirm the Node server is alive and responding.
  return new Response(JSON.stringify({ status: "OK", server: "Frontend" }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
    },
  });
}