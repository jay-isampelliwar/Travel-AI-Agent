export async function POST(request: Request) {
  const body = (await request.json()) as { message?: string };

  if (!body.message || typeof body.message !== "string") {
    return new Response("Invalid message", { status: 400 });
  }

  const backendResponse = await fetch(
    "https://sylvie-cytostomal-zeke.ngrok-free.dev/agent",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ user_message: body.message }),
    },
  );

  if (!backendResponse.ok || !backendResponse.body) {
    return new Response("Backend error", { status: 502 });
  }

  return new Response(backendResponse.body, {
    status: 200,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
}
