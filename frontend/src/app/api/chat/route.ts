export async function POST(request: Request) {
  const body = (await request.json()) as {
    message?: string;
    threadId?: string;
    sessionId?: string;
    userId?: string;
  };

  if (!body.message || typeof body.message !== "string") {
    return new Response("Invalid message", { status: 400 });
  }
  if (!body.threadId || typeof body.threadId !== "string") {
    return new Response("Invalid thread id", { status: 400 });
  }
  if (!body.sessionId || typeof body.sessionId !== "string") {
    return new Response("Invalid session id", { status: 400 });
  }
  if (!body.userId || typeof body.userId !== "string") {
    return new Response("Invalid user id", { status: 400 });
  }

  const prod = "https://sylvie-cytostomal-zeke.ngrok-free.dev/agent";
  const local = "http://127.0.0.1:8000/agent";

  const is_local = false;

  const backendUrl = is_local ? local : prod;

  const backendResponse = await fetch(backendUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_message: body.message,
      thread_id: body.threadId,
      session_id: body.sessionId,
      user_id: body.userId,
    }),
  });

  if (!backendResponse.ok) {
    return new Response("Backend error", { status: 502 });
  }

  // Backend now returns JSON: { message, ui_type, data, follow_up_questions }.
  const result = (await backendResponse.json()) as {
    message: string;
    ui_type: string | string[];
    data: unknown;
    follow_up_questions: string[];
  };

  return new Response(JSON.stringify(result), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
    },
  });
}
