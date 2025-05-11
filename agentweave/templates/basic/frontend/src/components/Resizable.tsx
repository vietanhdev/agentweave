import { useState, useEffect, useRef, useCallback, Children } from "react";
import { cn } from "@/lib/utils";

interface ResizableProps {
  defaultSize?: number;
  minSize?: number;
  maxSize?: number;
  side: "left" | "right";
  children: React.ReactNode;
  className?: string;
}

export function Resizable({
  defaultSize = 25,
  minSize = 15,
  maxSize = 50,
  side = "left",
  children,
  className,
}: ResizableProps) {
  const [size, setSize] = useState(defaultSize);
  const [isResizing, setIsResizing] = useState(false);
  const resizerRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Extract the two children
  const childrenArray = Children.toArray(children);
  const firstChild = childrenArray[0];
  const secondChild = childrenArray[1];

  // Start the resize operation
  const startResize = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsResizing(true);
    document.body.classList.add("resizing");
  }, []);

  // Stop the resize operation
  const stopResize = useCallback(() => {
    setIsResizing(false);
    document.body.classList.remove("resizing");
  }, []);

  // Handle the resize operation
  const resize = useCallback(
    (e: MouseEvent) => {
      if (!isResizing || !containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      const containerWidth = containerRect.width;

      // Calculate the new size as a percentage of the container width
      const newSizePixels =
        side === "left"
          ? e.clientX - containerRect.left
          : containerRect.right - e.clientX;

      const newSizePercent = (newSizePixels / containerWidth) * 100;

      // Constrain the size within the min and max limits
      const clampedSize = Math.max(minSize, Math.min(maxSize, newSizePercent));

      setSize(clampedSize);
    },
    [isResizing, minSize, maxSize, side],
  );

  // Set up event listeners for resize
  useEffect(() => {
    if (isResizing) {
      window.addEventListener("mousemove", resize);
      window.addEventListener("mouseup", stopResize);
    }

    return () => {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResize);
    };
  }, [isResizing, resize, stopResize]);

  return (
    <div ref={containerRef} className={cn("flex h-full", className)}>
      {/* The first panel - always on the left */}
      <div
        className="h-full overflow-hidden"
        style={{
          width: `${size}%`,
          transition: isResizing ? "none" : "width 0.1s ease",
        }}
      >
        {firstChild}
      </div>

      {/* The resizer handle */}
      <div
        ref={resizerRef}
        className={cn(
          "h-full w-1 bg-border hover:bg-primary/50 cursor-col-resize flex-shrink-0 touch-none select-none",
          isResizing && "bg-primary",
        )}
        onMouseDown={startResize}
      >
        <div className="h-8 w-1 bg-primary/70 rounded-full absolute top-1/2 -translate-y-1/2" />
      </div>

      {/* The second panel - always on the right */}
      <div className="h-full flex-1 overflow-hidden">{secondChild}</div>

      {/* Add global style for resizing cursor */}
      <style jsx global>{`
        body.resizing {
          cursor: col-resize !important;
          user-select: none;
        }
        body.resizing * {
          cursor: col-resize !important;
          user-select: none;
        }
      `}</style>
    </div>
  );
}
