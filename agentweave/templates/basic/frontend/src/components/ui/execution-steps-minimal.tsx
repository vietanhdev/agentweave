import { useState } from "react";
import {
  Clock,
  MessageSquare,
  Wrench,
  AlertCircle,
  ChevronRight,
  ChevronDown,
  Eye,
  ChevronsUpDown,
  Maximize,
  Minimize,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./button";
import { JsonView } from "react-json-view-lite";
import "react-json-view-lite/dist/index.css";

// Add custom CSS for JsonView
const jsonViewStyles = `
  .json-view-lite {
    font-size: 10px !important;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace !important;
    background-color: transparent !important;
  }

  .json-view-container {
    font-size: 12px !important;
    background-color: transparent !important;
  }
`;

interface ExecutionStep {
  id: number;
  type: "llm_call" | "tool_call";
  timestamp: string;
  status: "success" | "error";
  input: any;
  output?: string;
  error?: string;
  tool?: string;
  tool_id?: string;
  tool_calls?: Array<{ name: string; args: any }>;
}

interface ExecutionStepsMinimalProps {
  steps: ExecutionStep[];
  className?: string;
}

export function ExecutionStepsMinimal({
  steps,
  className,
}: ExecutionStepsMinimalProps) {
  const [expandedStepId, setExpandedStepId] = useState<number | null>(null);
  const [showFullInputOutput, setShowFullInputOutput] = useState<
    Record<number, boolean>
  >({});
  const [fullScreenData, setFullScreenData] = useState<{
    title: string;
    data: any;
  } | null>(null);

  if (!steps || steps.length === 0) {
    return null;
  }

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    } catch (e) {
      return timestamp;
    }
  };

  const formatToolName = (name?: string) => {
    if (!name) return "";
    // Convert camelCase or snake_case to Title Case with spaces
    return name
      .replace(/_/g, " ")
      .replace(/([A-Z])/g, " $1")
      .replace(/^\w/, (c) => c.toUpperCase())
      .trim();
  };

  const toggleExpand = (id: number) => {
    setExpandedStepId(expandedStepId === id ? null : id);
  };

  const toggleInputOutput = (id: number) => {
    setShowFullInputOutput((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const toggleFullScreen = (title: string, data: any) => {
    setFullScreenData(fullScreenData ? null : { title, data });
  };

  const getStepIcon = (step: ExecutionStep) => {
    if (step.status === "error") {
      return <AlertCircle className="h-3.5 w-3.5 text-destructive" />;
    }

    switch (step.type) {
      case "llm_call":
        return <MessageSquare className="h-3.5 w-3.5 text-primary/80" />;
      case "tool_call":
        return <Wrench className="h-3.5 w-3.5 text-blue-500" />;
      default:
        return <Clock className="h-3.5 w-3.5 text-muted-foreground" />;
    }
  };

  // Parse JSON string or return original object
  const parseJsonIfString = (value: any): any => {
    if (typeof value === "string") {
      try {
        return JSON.parse(value);
      } catch (e) {
        return value;
      }
    }
    return value;
  };

  // Format plain text for display
  const formatTextOutput = (text: string): string => {
    if (!text) return "";
    return text;
  };

  // Determine if content is probably JSON or an object
  const isJsonObject = (value: any): boolean => {
    if (typeof value === "object" && value !== null) return true;
    if (typeof value === "string") {
      try {
        const parsed = JSON.parse(value);
        return typeof parsed === "object" && parsed !== null;
      } catch (e) {
        return false;
      }
    }
    return false;
  };

  // Get a sample of text (for preview)
  const getTextSample = (text: string, maxLength: number = 300): string => {
    if (!text) return "";
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  };

  // Safely render JSON data
  const renderJsonData = (data: any) => {
    try {
      const parsedData = parseJsonIfString(data);
      // Ensure we're passing a valid object to JsonView
      if (parsedData !== null && typeof parsedData === "object") {
        return <JsonView data={parsedData} />;
      }
      // Fallback for non-object data
      return (
        <pre className="text-[10px] p-2 overflow-auto font-mono">
          {JSON.stringify(data, null, 2)}
        </pre>
      );
    } catch (e) {
      // If any error occurs, fallback to simple text rendering
      return (
        <pre className="text-[10px] p-2 overflow-auto font-mono">
          {String(data)}
        </pre>
      );
    }
  };

  const renderInputOutput = (step: ExecutionStep) => {
    const isFullView = showFullInputOutput[step.id] || false;

    return (
      <div className="space-y-3 mt-2">
        {/* Input Section */}
        {step.input && Object.keys(step.input).length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-1">
              <div className="text-xs font-medium text-muted-foreground">
                Input:
              </div>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 px-2 py-1 text-xs"
                  onClick={() => toggleInputOutput(step.id)}
                >
                  {isFullView ? "Collapse" : "Expand"}
                  <ChevronsUpDown className="ml-1 h-3 w-3" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={() =>
                    toggleFullScreen(
                      "Input Data",
                      parseJsonIfString(step.input),
                    )
                  }
                >
                  <Maximize className="h-3 w-3" />
                </Button>
              </div>
            </div>
            <div
              className={cn(
                "bg-muted/40 rounded overflow-hidden transition-all",
                isFullView ? "max-h-96" : "max-h-28",
              )}
            >
              {isJsonObject(step.input) ? (
                <div
                  className="p-1 overflow-auto"
                  style={{ maxHeight: isFullView ? "24rem" : "7rem" }}
                >
                  <div className="json-view-lite">
                    {renderJsonData(step.input)}
                  </div>
                </div>
              ) : (
                <pre className="text-[10px] p-2 overflow-auto font-mono">
                  {typeof step.input === "string"
                    ? isFullView
                      ? step.input
                      : getTextSample(step.input)
                    : JSON.stringify(step.input, null, 2)}
                </pre>
              )}
            </div>
          </div>
        )}

        {/* Output Section */}
        {step.output && (
          <div>
            <div className="flex items-center justify-between mb-1">
              <div className="text-xs font-medium text-muted-foreground">
                Output:
              </div>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 px-2 py-1 text-xs"
                  onClick={() => toggleInputOutput(step.id)}
                >
                  {isFullView ? "Collapse" : "Expand"}
                  <ChevronsUpDown className="ml-1 h-3 w-3" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={() =>
                    toggleFullScreen(
                      "Output Data",
                      parseJsonIfString(step.output),
                    )
                  }
                >
                  <Maximize className="h-3 w-3" />
                </Button>
              </div>
            </div>
            <div
              className={cn(
                "bg-muted/40 rounded overflow-hidden transition-all",
                isFullView ? "max-h-96" : "max-h-28",
              )}
            >
              {isJsonObject(step.output) ? (
                <div
                  className="p-1 overflow-auto"
                  style={{ maxHeight: isFullView ? "24rem" : "7rem" }}
                >
                  <div className="json-view-lite">
                    {renderJsonData(step.output)}
                  </div>
                </div>
              ) : (
                <pre className="text-[10px] p-2 overflow-auto font-mono">
                  {typeof step.output === "string"
                    ? isFullView
                      ? step.output
                      : getTextSample(step.output)
                    : JSON.stringify(step.output, null, 2)}
                </pre>
              )}
            </div>
          </div>
        )}

        {/* Error Section */}
        {step.error && (
          <div>
            <div className="text-xs font-medium text-destructive mb-1">
              Error:
            </div>
            <div className="bg-destructive/10 rounded p-2">
              <pre className="text-[10px] text-destructive overflow-auto font-mono">
                {step.error}
              </pre>
            </div>
          </div>
        )}

        {/* Tool Calls Section */}
        {step.tool_calls && step.tool_calls.length > 0 && (
          <div>
            <div className="text-xs font-medium text-muted-foreground mb-1">
              Tool Calls:
            </div>
            <div className="space-y-2">
              {step.tool_calls.map((call, idx) => (
                <div key={idx} className="bg-muted/30 rounded p-2">
                  <div className="flex items-center justify-between">
                    <div className="text-[10px] font-medium">
                      {formatToolName(call.name)}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-5 w-5 p-0"
                      onClick={() =>
                        toggleFullScreen(
                          `Tool Call: ${formatToolName(call.name)}`,
                          call.args,
                        )
                      }
                    >
                      <Maximize className="h-3 w-3" />
                    </Button>
                  </div>
                  <div
                    className="mt-1 overflow-hidden"
                    style={{ maxHeight: "7rem" }}
                  >
                    {isJsonObject(call.args) ? (
                      <div className="json-view-lite">
                        {renderJsonData(call.args)}
                      </div>
                    ) : (
                      <div className="text-[10px] font-mono overflow-auto">
                        {typeof call.args === "string"
                          ? call.args
                          : JSON.stringify(call.args, null, 2)}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      <style jsx global>
        {jsonViewStyles}
      </style>
      <div className={cn("text-sm", className)}>
        <div className="space-y-1.5">
          {steps.map((step) => (
            <div
              key={step.id}
              className={cn(
                "border-l-2 pl-3 pb-1 transition-colors",
                step.status === "error"
                  ? "border-destructive"
                  : "border-muted-foreground/30",
                expandedStepId === step.id && "border-primary/80",
              )}
            >
              <button
                onClick={() => toggleExpand(step.id)}
                className={cn(
                  "flex items-center gap-2 w-full text-left mb-1 hover:bg-muted/50 rounded px-1 py-0.5 transition-colors",
                  expandedStepId === step.id && "bg-muted/70",
                )}
              >
                <div className="flex-shrink-0">{getStepIcon(step)}</div>

                <div className="flex-1 truncate font-medium">
                  {step.type === "llm_call"
                    ? "Thinking"
                    : step.tool
                      ? formatToolName(step.tool)
                      : "Tool Call"}
                </div>

                <div className="text-xs text-muted-foreground flex items-center gap-1.5">
                  <span className="opacity-70">
                    {formatTime(step.timestamp)}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-5 w-5 p-0"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleInputOutput(step.id);
                    }}
                  >
                    <Eye className="h-3 w-3" />
                    <span className="sr-only">Toggle details</span>
                  </Button>
                  {expandedStepId === step.id ? (
                    <ChevronDown className="h-3 w-3" />
                  ) : (
                    <ChevronRight className="h-3 w-3" />
                  )}
                </div>
              </button>

              {expandedStepId === step.id && (
                <div className="pl-1 pr-2 py-1.5 text-xs">
                  {step.type === "tool_call" && step.tool && (
                    <div className="mb-1.5">
                      <span className="text-muted-foreground">Tool:</span>{" "}
                      <span className="font-medium">
                        {formatToolName(step.tool)}
                      </span>
                    </div>
                  )}

                  {/* Render the input and output details */}
                  {renderInputOutput(step)}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Fullscreen JSON viewer modal */}
      {fullScreenData && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-background border rounded-lg shadow-lg w-full max-w-5xl h-[80vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="font-semibold">{fullScreenData.title}</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setFullScreenData(null)}
              >
                <Minimize className="h-4 w-4" />
                <span className="ml-2">Close</span>
              </Button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              {isJsonObject(fullScreenData.data) ? (
                <div className="json-view-container">
                  {renderJsonData(fullScreenData.data)}
                </div>
              ) : (
                <pre className="text-sm font-mono whitespace-pre-wrap">
                  {fullScreenData.data}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
