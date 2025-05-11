"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  Code,
  History,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  Hammer,
  FileUp,
  FileX,
  Trash,
  Eye,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";
import { ExecutionSteps } from "@/components/ui/execution-steps";
import { ExecutionStepsMinimal } from "@/components/ui/execution-steps-minimal";
import { ChatMessage } from "@/components/ChatMessage";
import { TypingIndicator } from "@/components/TypingIndicator";
import { Header } from "@/components/Header";
import { Resizable } from "@/components/Resizable";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

// Import our API hooks
import {
  useTools,
  useToggleTool,
  useDocuments,
  useSendQuery,
  useUploadDocument,
  useDeleteDocument,
} from "@/lib/api";
import { DocumentViewer } from "@/components/DocumentViewer";

interface Message {
  role: "user" | "assistant";
  content: string;
}

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

interface Tool {
  name: string;
  description: string;
  parameters: any;
  required_parameters: string[];
  enabled: boolean;
}

interface Document {
  id: string;
  filename: string;
  size: number;
  type: string;
  description?: string;
  ingestion_status?: {
    processed: boolean;
    error?: string;
  };
  chunk_count?: number;
  tags?: string[];
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I'm an AI assistant for {{project_name}}. How can I help you today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [executionSteps, setExecutionSteps] = useState<ExecutionStep[]>([]);
  const [isStepsVisible, setIsStepsVisible] = useState(true);
  const [activeTab, setActiveTab] = useState("steps");
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  const [fileDescription, setFileDescription] = useState("");
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(
    null,
  );
  const [isDocumentViewerOpen, setIsDocumentViewerOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // Use SWR hooks for data fetching
  const { data: toolsData, isLoading: isToolsLoading } = useTools();
  const {
    data: documentsData,
    isLoading: isDocumentsLoading,
    mutate: refreshDocuments,
  } = useDocuments();
  const { sendQuery, isLoading: isQueryLoading } = useSendQuery();
  const { uploadDocument: uploadDocumentApi, isLoading: isUploadLoading } =
    useUploadDocument();
  const { deleteDocument: deleteDocumentApi, isLoading: isDeleteLoading } =
    useDeleteDocument();
  const { toggleTool: handleToggleTool } = useToggleTool();

  // Extract data from SWR responses
  const tools = toolsData?.tools || [];
  const documents = documentsData?.documents || [];

  // Scroll to bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    // Add user message to state
    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      // Send API request using our hook
      const data = await sendQuery({
        query: input,
        conversation_id: conversationId,
      });

      // Update conversation ID if not set
      if (!conversationId) {
        setConversationId(data.conversation_id);
      }

      // Update execution steps if available
      if (data.metadata && data.metadata.execution_steps) {
        setExecutionSteps(data.metadata.execution_steps);
        // Ensure execution steps panel is visible when new steps arrive
        setIsStepsVisible(true);
      }

      // Add response to messages
      const assistantMessage: Message = {
        role: "assistant",
        content: data.response,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      // Error handling is done inside the hook
      console.error("Error in chat:", error);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleStepsVisibility = () => {
    setIsStepsVisible(!isStepsVisible);
  };

  const handleUploadDocument = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!fileInputRef.current?.files?.length) {
      toast({
        title: "Error",
        description: "Please select a file to upload",
        variant: "destructive",
      });
      return;
    }

    const file = fileInputRef.current.files[0];

    try {
      await uploadDocumentApi(file, {
        description: fileDescription,
        tags: [], // You could add a field for tags
        category: "", // You could add a field for category
      });

      // Refresh documents list
      refreshDocuments();

      // Reset form and close dialog
      setFileDescription("");
      setIsUploadDialogOpen(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      toast({
        title: "Success",
        description: "Document uploaded successfully",
      });
    } catch (error) {
      // Error handling is done inside the hook
      console.error("Upload error:", error);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    try {
      await deleteDocumentApi(docId);

      // Refresh documents list
      refreshDocuments();

      toast({
        title: "Success",
        description: "Document deleted successfully",
      });
    } catch (error) {
      // Error handling is done inside the hook
      console.error("Delete error:", error);
    }
  };

  const handleViewDocument = (doc: Document) => {
    setSelectedDocument(doc);
    setIsDocumentViewerOpen(true);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " bytes";
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    else return (bytes / 1048576).toFixed(1) + " MB";
  };

  const renderSidebarContent = () => {
    switch (activeTab) {
      case "steps":
        return executionSteps.length ? (
          <ExecutionStepsMinimal steps={executionSteps} />
        ) : (
          <div className="text-muted-foreground text-center py-8">
            <Code className="mx-auto h-6 w-6 mb-2 opacity-40" />
            <p className="text-xs">No execution steps yet</p>
          </div>
        );
      case "tools":
        if (isToolsLoading) {
          return (
            <div className="text-muted-foreground text-center py-8">
              <Hammer className="mx-auto h-6 w-6 mb-2 opacity-40 animate-pulse" />
              <p className="text-xs">Loading tools...</p>
            </div>
          );
        }

        if (!tools.length) {
          return (
            <div className="text-muted-foreground text-center py-8">
              <Hammer className="mx-auto h-6 w-6 mb-2 opacity-40" />
              <p className="text-xs">No tools available</p>
            </div>
          );
        }

        return (
          <div className="space-y-3">
            {tools.map((tool, index) => (
              <Card key={index} className="p-3 text-sm">
                <div className="font-medium flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Hammer
                      className={`h-3.5 w-3.5 ${
                        !tool.enabled ? "opacity-40" : ""
                      }`}
                    />
                    <span
                      className={!tool.enabled ? "text-muted-foreground" : ""}
                    >
                      {tool.name}
                    </span>
                  </div>
                  <Switch
                    checked={tool.enabled}
                    onCheckedChange={(checked) => {
                      handleToggleTool(tool.name, checked);
                    }}
                    aria-label={`${tool.enabled ? "Disable" : "Enable"} ${
                      tool.name
                    }`}
                  />
                </div>
                <p
                  className={`text-xs ${
                    !tool.enabled
                      ? "text-muted-foreground/70"
                      : "text-muted-foreground"
                  } mt-1`}
                >
                  {tool.description}
                </p>
              </Card>
            ))}
          </div>
        );
      case "documents":
        return (
          <div className="space-y-3">
            <div className="flex justify-end">
              <Dialog
                open={isUploadDialogOpen}
                onOpenChange={setIsUploadDialogOpen}
              >
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm" className="h-7 text-xs">
                    <FileUp className="h-3 w-3 mr-1" /> Upload
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Upload Document</DialogTitle>
                    <DialogDescription>
                      Add documents to the agent's knowledge base
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleUploadDocument}>
                    <div className="grid gap-4 py-4">
                      <div className="grid gap-2">
                        <Label htmlFor="file">File</Label>
                        <Input
                          id="file"
                          type="file"
                          ref={fileInputRef}
                          required
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="description">
                          Description (optional)
                        </Label>
                        <Input
                          id="description"
                          value={fileDescription}
                          onChange={(e) => setFileDescription(e.target.value)}
                          placeholder="Brief description of the document"
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button type="submit" disabled={isUploadLoading}>
                        {isUploadLoading ? "Uploading..." : "Upload"}
                      </Button>
                    </DialogFooter>
                  </form>
                </DialogContent>
              </Dialog>
            </div>

            {isDocumentsLoading ? (
              <div className="text-muted-foreground text-center py-8">
                <FileUp className="mx-auto h-6 w-6 mb-2 opacity-40 animate-pulse" />
                <p className="text-xs">Loading documents...</p>
              </div>
            ) : documents.length > 0 ? (
              documents.map((doc, index) => (
                <Card key={index} className="p-3 text-sm">
                  <div className="font-medium flex items-center justify-between">
                    <div className="flex items-center gap-2 truncate">
                      <FileUp className="h-3.5 w-3.5 shrink-0" />
                      <span className="truncate">{doc.filename}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={() => handleViewDocument(doc)}
                      >
                        <Eye className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={() => handleDeleteDocument(doc.id)}
                        disabled={isDeleteLoading}
                      >
                        <Trash className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                  <div className="flex justify-between items-center mt-1">
                    <span className="text-xs text-muted-foreground">
                      {formatFileSize(doc.size)}
                    </span>
                    {doc.description && (
                      <span className="text-xs text-muted-foreground truncate max-w-[70%]">
                        {doc.description}
                      </span>
                    )}
                  </div>
                  {doc.ingestion_status && (
                    <div className="mt-1 text-xs">
                      <div className="flex items-center gap-1">
                        <div
                          className={`w-2 h-2 rounded-full ${
                            doc.ingestion_status.processed
                              ? "bg-green-500"
                              : "bg-red-500"
                          }`}
                        />
                        <span
                          className={
                            doc.ingestion_status.processed
                              ? "text-green-500"
                              : "text-red-500"
                          }
                        >
                          {doc.ingestion_status.processed
                            ? "Processed"
                            : "Failed"}
                        </span>
                        {doc.chunk_count !== undefined && (
                          <span className="text-muted-foreground ml-2">
                            ({doc.chunk_count} chunks)
                          </span>
                        )}
                      </div>
                      {doc.ingestion_status.error && (
                        <div className="text-red-500 mt-1 text-[10px]">
                          Error: {doc.ingestion_status.error}
                        </div>
                      )}
                    </div>
                  )}
                  {doc.tags && doc.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {doc.tags.map((tag, i) => (
                        <span
                          key={i}
                          className="bg-primary/10 text-primary text-[10px] px-1.5 py-0.5 rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </Card>
              ))
            ) : (
              <div className="text-muted-foreground text-center py-8">
                <FileX className="mx-auto h-6 w-6 mb-2 opacity-40" />
                <p className="text-xs">No documents uploaded</p>
              </div>
            )}
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <>
      <Header />
      <main className="flex-1 container p-4 md:py-6">
        {/* Document viewer */}
        {selectedDocument && (
          <DocumentViewer
            documentId={selectedDocument.id}
            documentName={selectedDocument.filename}
            isOpen={isDocumentViewerOpen}
            onClose={() => setIsDocumentViewerOpen(false)}
          />
        )}

        <div className="h-[calc(100vh-12rem)]">
          <Card className="shadow-sm border-muted/40 h-full flex flex-col">
            <CardHeader className="py-3 px-4 flex flex-row items-center justify-between border-b">
              <CardTitle className="text-xl">Chat</CardTitle>
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleStepsVisibility}
                className="md:hidden"
                aria-label={isStepsVisible ? "Hide sidebar" : "Show sidebar"}
              >
                {isStepsVisible ? (
                  <ChevronRight className="h-5 w-5" />
                ) : (
                  <ChevronLeft className="h-5 w-5" />
                )}
              </Button>
            </CardHeader>

            <CardContent className="p-0 flex-1 overflow-hidden">
              {/* Desktop: Resizable layout */}
              <div className="h-full hidden md:block">
                <Resizable
                  defaultSize={25}
                  minSize={20}
                  maxSize={40}
                  side="left"
                >
                  {/* Left Side: Sidebar Panel with Tabs */}
                  <Card className="rounded-none border-0 border-r h-full flex flex-col bg-muted/10">
                    <CardHeader className="py-2 px-3">
                      <Tabs defaultValue="steps" onValueChange={setActiveTab}>
                        <TabsList className="grid grid-cols-3">
                          <TabsTrigger value="steps">Steps</TabsTrigger>
                          <TabsTrigger value="tools">Tools</TabsTrigger>
                          <TabsTrigger value="documents">Docs</TabsTrigger>
                        </TabsList>
                      </Tabs>
                    </CardHeader>
                    <CardContent className="p-0 flex-1 overflow-hidden border-t">
                      <ScrollArea className="h-full">
                        <div className="p-2">{renderSidebarContent()}</div>
                      </ScrollArea>
                    </CardContent>
                  </Card>

                  {/* Right Side: Chat Panel */}
                  <div className="h-full flex flex-col">
                    <div className="flex-1 overflow-hidden">
                      <ScrollArea className="h-full">
                        <div className="flex flex-col gap-6 p-4 md:p-6">
                          {messages.map((message, index) => (
                            <ChatMessage
                              key={index}
                              content={message.content}
                              role={message.role}
                            />
                          ))}
                          {isQueryLoading && <TypingIndicator />}
                          <div ref={messagesEndRef} />
                        </div>
                      </ScrollArea>
                    </div>

                    <div className="p-4 pt-2 border-t">
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          handleSend();
                        }}
                        className="flex w-full gap-2"
                      >
                        <Input
                          placeholder="Type your message..."
                          value={input}
                          onChange={(e) => setInput(e.target.value)}
                          onKeyDown={handleKeyDown}
                          disabled={isQueryLoading}
                          className="border-muted/60 focus-visible:ring-primary/30"
                        />
                        <Button
                          disabled={isQueryLoading}
                          type="submit"
                          size="icon"
                          className="shrink-0"
                        >
                          <Send className="h-4 w-4" />
                        </Button>
                      </form>
                    </div>
                  </div>
                </Resizable>
              </div>

              {/* Mobile: Stack layout */}
              <div className="h-full md:hidden">
                {isStepsVisible ? (
                  <div className="h-full flex flex-col">
                    <div className="p-3 border-b">
                      <Tabs defaultValue="steps" onValueChange={setActiveTab}>
                        <TabsList className="grid grid-cols-3">
                          <TabsTrigger value="steps">Steps</TabsTrigger>
                          <TabsTrigger value="tools">Tools</TabsTrigger>
                          <TabsTrigger value="documents">Docs</TabsTrigger>
                        </TabsList>
                      </Tabs>
                      <div className="flex justify-between items-center mt-2">
                        <div className="text-sm font-medium flex items-center gap-2">
                          {activeTab === "steps" && (
                            <Code className="h-3.5 w-3.5" />
                          )}
                          {activeTab === "tools" && (
                            <Hammer className="h-3.5 w-3.5" />
                          )}
                          {activeTab === "documents" && (
                            <FileUp className="h-3.5 w-3.5" />
                          )}
                          {activeTab === "steps"
                            ? "Execution Steps"
                            : activeTab === "tools"
                              ? "Available Tools"
                              : "Documents"}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={toggleStepsVisibility}
                          className="h-7 px-2"
                        >
                          <span className="sr-only">Show chat</span>
                          <ChevronRight className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    <ScrollArea className="flex-1">
                      <div className="p-2">{renderSidebarContent()}</div>
                    </ScrollArea>
                  </div>
                ) : (
                  <div className="h-full flex flex-col">
                    <div className="flex-1 overflow-hidden">
                      <ScrollArea className="h-full">
                        <div className="flex flex-col gap-6 p-4">
                          {messages.map((message, index) => (
                            <ChatMessage
                              key={index}
                              content={message.content}
                              role={message.role}
                            />
                          ))}
                          {isQueryLoading && <TypingIndicator />}
                          <div ref={messagesEndRef} />
                        </div>
                      </ScrollArea>
                    </div>

                    <div className="p-4 pt-2 border-t">
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          handleSend();
                        }}
                        className="flex w-full gap-2"
                      >
                        <Input
                          placeholder="Type your message..."
                          value={input}
                          onChange={(e) => setInput(e.target.value)}
                          onKeyDown={handleKeyDown}
                          disabled={isQueryLoading}
                          className="border-muted/60 focus-visible:ring-primary/30"
                        />
                        <Button
                          disabled={isQueryLoading}
                          type="submit"
                          size="icon"
                          className="shrink-0"
                        >
                          <Send className="h-4 w-4" />
                        </Button>
                      </form>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </>
  );
}
