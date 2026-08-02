"use client";

import React, { useState, useCallback, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FileItem {
  file: File;
  previewUrl: string;
  type: "image" | "pdf";
}

export default function FinancialReport() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<string | null>(null);
  const [pagesProcessed, setPagesProcessed] = useState(0);
  const [extractedTexts, setExtractedTexts] = useState<string[]>([]);
  const [showExtracted, setShowExtracted] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFilesSelected = useCallback(
    (newFiles: FileList | File[]) => {
      const items: FileItem[] = [...files];
      for (const file of Array.from(newFiles)) {
        const allowed = [
          "application/pdf",
          "image/png",
          "image/jpeg",
          "image/jpg",
          "image/webp",
        ];
        if (!allowed.includes(file.type)) continue;
        items.push({
          file,
          previewUrl: URL.createObjectURL(file),
          type: file.type === "application/pdf" ? "pdf" : "image",
        });
      }
      setFiles(items);
      setError(null);
    },
    [files],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (e.dataTransfer.files.length > 0) {
        handleFilesSelected(e.dataTransfer.files);
      }
    },
    [handleFilesSelected],
  );

  const removeFile = useCallback(
    (index: number) => {
      const updated = [...files];
      URL.revokeObjectURL(updated[index].previewUrl);
      updated.splice(index, 1);
      setFiles(updated);
    },
    [files],
  );

  const handleGenerate = useCallback(async () => {
    if (files.length === 0) return;
    setIsProcessing(true);
    setError(null);
    setReport(null);
    setExtractedTexts([]);

    try {
      const formData = new FormData();
      files.forEach((f) => formData.append("files", f.file));

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10 * 60 * 1000);

      const response = await fetch(`${API_URL}/api/report`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const err = await response.json().catch(() => null);
        throw new Error(err?.detail || `Server error: ${response.status}`);
      }

      const result = await response.json();
      setReport(result.report || "No report generated.");
      setPagesProcessed(result.pages_processed || 0);
      setExtractedTexts(result.extracted_texts || []);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "An unexpected error occurred",
      );
    } finally {
      setIsProcessing(false);
    }
  }, [files]);

  const handleReset = useCallback(() => {
    files.forEach((f) => URL.revokeObjectURL(f.previewUrl));
    setFiles([]);
    setReport(null);
    setError(null);
    setExtractedTexts([]);
    setShowExtracted(false);
    setPagesProcessed(0);
  }, [files]);

  // ── Upload zone ──
  const uploadZone = (
    <div
      className={`upload-zone ${files.length > 0 ? "has-file" : ""}`}
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      onClick={() => fileInputRef.current?.click()}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg,.webp"
        multiple
        onChange={(e) => {
          if (e.target.files) handleFilesSelected(e.target.files);
          e.target.value = "";
        }}
        style={{ display: "none" }}
      />
      <div style={{ position: "relative", zIndex: 1 }}>
        <div className="animate-float" style={{ fontSize: "3rem", opacity: 0.7 }}>
          📊
        </div>
        <p style={{ fontSize: "1.1rem", fontWeight: 600, margin: "1rem 0 0" }}>
          Drop your financial documents here
        </p>
        <p style={{ fontSize: "0.875rem", color: "var(--foreground-muted)", margin: "0.5rem 0 0" }}>
          Bank statements, invoices, receipts • PDF, PNG, JPG • Multiple files supported
        </p>
      </div>
    </div>
  );

  // ── File list ──
  const fileList = files.length > 0 && (
    <div className="glass-card" style={{ padding: "1rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
        <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>
          📎 {files.length} document{files.length !== 1 ? "s" : ""} selected
        </span>
        <button className="btn btn-ghost" onClick={() => fileInputRef.current?.click()} style={{ fontSize: "0.8rem" }}>
          + Add more
        </button>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {files.map((f, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              padding: "0.5rem 0.75rem",
              background: "var(--background-secondary)",
              borderRadius: "var(--radius-sm)",
            }}
          >
            <span style={{ fontSize: "1.2rem", flexShrink: 0 }}>
              {f.type === "pdf" ? "📄" : "🖼️"}
            </span>
            <span style={{ flex: 1, fontSize: "0.85rem", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {f.file.name}
            </span>
            <span style={{ fontSize: "0.75rem", color: "var(--foreground-muted)", flexShrink: 0 }}>
              {(f.file.size / 1024).toFixed(0)} KB
            </span>
            <button
              onClick={(e) => { e.stopPropagation(); removeFile(i); }}
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                color: "var(--foreground-muted)",
                fontSize: "1rem",
                padding: "0 0.25rem",
                flexShrink: 0,
              }}
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  // ── Processing indicator ──
  const processingCard = isProcessing && (
    <div className="glass-card animate-slide-up" style={{ padding: "2rem", textAlign: "center" }}>
      <div className="processing-spinner" style={{ margin: "0 auto 1rem" }} />
      <p className="processing-label">
        Processing {files.length} document{files.length !== 1 ? "s" : ""}…
      </p>
      <div className="processing-steps" style={{ justifyContent: "center" }}>
        <div className="processing-step active">
          <span className="step-dot" />
          <span>OCR extraction</span>
        </div>
        <div className="processing-step">
          <span className="step-dot" />
          <span>Generating report</span>
        </div>
      </div>
    </div>
  );

  // ── Report display ──
  const reportCard = report && (
    <div className="animate-slide-up" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {/* Stats bar */}
      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
        <span className="badge badge-success">✓ Report generated</span>
        <span className="badge badge-success">{pagesProcessed} pages processed</span>
        <span className="badge badge-success">{files.length} files</span>
      </div>

      {/* Markdown report */}
      <div className="glass-card report-content" style={{ padding: "2rem" }}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
      </div>

      {/* Extracted texts toggle */}
      <button
        className="btn btn-ghost"
        onClick={() => setShowExtracted(!showExtracted)}
        style={{ alignSelf: "flex-start" }}
      >
        {showExtracted ? "▼" : "▶"} Raw OCR Text ({extractedTexts.length} documents)
      </button>

      {showExtracted && (
        <div className="glass-card" style={{ padding: "1rem" }}>
          <pre style={{
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            fontSize: "0.8rem",
            color: "var(--foreground-secondary)",
            fontFamily: "var(--font-mono)",
            maxHeight: "400px",
            overflow: "auto",
            margin: 0,
          }}>
            {extractedTexts.join("\n\n")}
          </pre>
        </div>
      )}
    </div>
  );

  return (
    <div style={{ width: "100%", maxWidth: "900px", margin: "0 auto", padding: "2rem 1.5rem 3rem" }}>
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: "2rem" }}>
        <h1 style={{
          fontSize: "1.8rem",
          fontWeight: 700,
          margin: "0 0 0.5rem 0",
          background: "linear-gradient(135deg, var(--foreground) 0%, var(--color-primary) 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}>
          Financial Report AI
        </h1>
        <p style={{ color: "var(--foreground-secondary)", margin: 0, fontSize: "0.95rem" }}>
          Upload bank statements, invoices, or receipts and let AI generate a financial report for you.
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        {/* Upload zone — always visible when no report */}
        {!report && uploadZone}
        {!report && fileList}

        {/* Error */}
        {error && (
          <div className="glass-card" style={{ padding: "1rem", borderColor: "rgba(248, 113, 113, 0.3)" }}>
            <p style={{ color: "var(--color-error)", margin: 0, fontWeight: 600 }}>{error}</p>
          </div>
        )}

        {/* Processing */}
        {processingCard}

        {/* Generate button */}
        {!report && files.length > 0 && !isProcessing && (
          <button
            className="btn btn-primary"
            onClick={handleGenerate}
            style={{ alignSelf: "center", minWidth: "220px", padding: "0.875rem 2rem", fontSize: "1rem" }}
          >
            📊 Generate Report
          </button>
        )}

        {/* Report */}
        {reportCard}

        {/* Reset */}
        {(report || files.length > 0) && !isProcessing && (
          <button className="btn btn-ghost" onClick={handleReset} style={{ alignSelf: "center" }}>
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
