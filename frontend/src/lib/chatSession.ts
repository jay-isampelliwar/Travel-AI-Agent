export type ChatSessionContext = {
  userId: string;
  sessionId: string;
  threadId: string;
};

function createId(prefix: string): string {
  return `${prefix}_${crypto.randomUUID()}`;
}

export function createChatSession(userName: string): ChatSessionContext {
  return {
    userId: userName.trim(),
    sessionId: createId("session"),
    threadId: createId("thread"),
  };
}
