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

  if (!backendResponse.ok) {
    return new Response("Backend error", { status: 502 });
  }

  // Backend now returns JSON: { message, ui_type, data, follow_up_questions }.
  // For the existing UI, we only forward the `message` field as plain text.
  const result = (await backendResponse.json()) as {
    message: string;
    ui_type: string;
    data: unknown;
    follow_up_questions: string[];
  };

  return new Response(JSON.stringify(result.message), {
    status: 200,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
}
