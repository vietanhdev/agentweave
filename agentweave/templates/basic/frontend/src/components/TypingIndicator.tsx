import { cn } from "@/lib/utils";

interface TypingIndicatorProps {
  className?: string;
}

export function TypingIndicator({ className }: TypingIndicatorProps) {
  return (
    <div className={cn("flex justify-start animate-in fade-in", className)}>
      <div className="bg-muted rounded-lg px-4 py-3 shadow-sm flex gap-2 items-center">
        <div className="flex space-x-1.5">
          <div className="h-2 w-2 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:-0.3s]"></div>
          <div className="h-2 w-2 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:-0.15s]"></div>
          <div className="h-2 w-2 rounded-full bg-muted-foreground/50 animate-bounce"></div>
        </div>
        <span className="text-muted-foreground/70 text-sm">Thinking</span>
      </div>
    </div>
  );
}
