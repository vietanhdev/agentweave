import { useState } from "react";
import {
  Clock,
  Terminal,
  MessageSquare,
  Wrench,
  AlertCircle,
  ChevronDown,
} from "lucide-react";

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

interface ExecutionStepsProps {
  steps: ExecutionStep[];
}

export function ExecutionSteps({ steps }: ExecutionStepsProps) {
  const [openSteps, setOpenSteps] = useState<Record<number, boolean>>({});

  if (!steps || steps.length === 0) {
    return null;
  }

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString();
    } catch (e) {
      return timestamp;
    }
  };

  const formatJson = (obj: any) => {
    try {
      if (typeof obj === "string") {
        return obj;
      }
      return JSON.stringify(obj, null, 2);
    } catch (e) {
      return String(obj);
    }
  };

  const toggleStep = (id: number) => {
    setOpenSteps((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  return (
    <div className="mt-4 border rounded-lg shadow-sm">
      <div className="p-4 border-b">
        <h3 className="text-lg flex items-center gap-2 font-medium">
          <Terminal className="h-4 w-4" />
          Execution Steps
        </h3>
        <p className="text-sm text-gray-500">
          Step-by-step execution of the agent's thought process
        </p>
      </div>
      <div className="p-4">
        {steps.map((step) => (
          <div key={step.id} className="mb-2 border rounded-lg overflow-hidden">
            <button
              className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-50"
              onClick={() => toggleStep(step.id)}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    step.status === "success"
                      ? "bg-green-100 text-green-800"
                      : "bg-red-100 text-red-800"
                  }`}
                >
                  {step.id}
                </span>
                {step.type === "llm_call" ? (
                  <MessageSquare className="h-4 w-4" />
                ) : (
                  <Wrench className="h-4 w-4" />
                )}

                <span className="font-medium">
                  {step.type === "llm_call"
                    ? "LLM Call"
                    : `Tool: ${step.tool || "Unknown"}`}
                </span>

                {step.status === "error" && (
                  <AlertCircle className="h-4 w-4 text-red-500 ml-2" />
                )}
              </div>

              <div className="flex items-center">
                <span className="text-gray-500 text-xs flex items-center mr-2">
                  <Clock className="h-3 w-3 mr-1" />
                  {formatTime(step.timestamp)}
                </span>
                <ChevronDown
                  className={`h-4 w-4 transition-transform ${
                    openSteps[step.id] ? "rotate-180" : ""
                  }`}
                />
              </div>
            </button>

            {openSteps[step.id] && (
              <div className="p-3 border-t bg-gray-50">
                <div className="mb-2">
                  <h4 className="text-sm font-medium mb-1">Input</h4>
                  <div className="bg-white p-2 rounded-md border">
                    <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-60">
                      {formatJson(step.input)}
                    </pre>
                  </div>
                </div>

                {(step.output || step.error) && (
                  <div className="mb-2">
                    <h4 className="text-sm font-medium mb-1">
                      {step.status === "success" ? "Output" : "Error"}
                    </h4>
                    <div
                      className={`p-2 rounded-md border ${
                        step.error ? "bg-red-50" : "bg-white"
                      }`}
                    >
                      <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-60">
                        {step.error || step.output}
                      </pre>
                    </div>
                  </div>
                )}

                {step.tool_calls && step.tool_calls.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-1">Tool Calls</h4>
                    {step.tool_calls.map((toolCall, idx) => (
                      <div
                        key={idx}
                        className="mb-2 border rounded-md p-2 bg-white"
                      >
                        <div className="font-medium text-sm mb-1">
                          Tool: {toolCall.name}
                        </div>
                        <div className="bg-gray-50 p-2 rounded-md border">
                          <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-40">
                            {formatJson(toolCall.args)}
                          </pre>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
