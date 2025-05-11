import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";

interface ChatMessageProps {
  content: string;
  role: "user" | "assistant";
  timestamp?: string;
}

export function ChatMessage({ content, role, timestamp }: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div
      className={cn(
        "flex animate-in fade-in duration-200",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      <div
        className={cn(
          "rounded-lg px-4 py-3 max-w-[85%] shadow-sm",
          isUser
            ? "bg-primary" // The global CSS will handle text color
            : "bg-muted text-muted-foreground",
        )}
      >
        <div className="prose prose-sm md:prose-base max-w-none">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
        {timestamp && (
          <div className="mt-2 text-xs opacity-70 text-right">{timestamp}</div>
        )}
      </div>
    </div>
  );
}
