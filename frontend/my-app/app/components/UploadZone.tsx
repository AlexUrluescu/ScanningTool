"use client";

import React, { useCallback, useRef, useState } from "react";

interface UploadZoneProps {
  onFileSelected: (file: File) => void;
  isProcessing: boolean;
  selectedFile: File | null;
}

const ACCEPTED_TYPES = [
  "application/pdf",
  "image/png",
  "image/jpeg",
  "image/webp",
];

const MAX_SIZE_MB = 10;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

export default function UploadZone({
  onFileSelected,
  isProcessing,
  selectedFile,
}: UploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback((file: File): string | null => {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      return `Unsupported file type: ${file.type}. Please upload PDF, PNG, JPG, or WEBP files.`;
    }
    if (file.size > MAX_SIZE_BYTES) {
      return `File too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Maximum size is ${MAX_SIZE_MB} MB.`;
    }
    return null;
  }, []);

  const handleFile = useCallback(
    (file: File) => {
      setError(null);
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }
      onFileSelected(file);
    },
    [onFileSelected, validateFile]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleClick = useCallback(() => {
    if (!isProcessing) inputRef.current?.click();
  }, [isProcessing]);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (type: string): string => {
    if (type === "application/pdf") return "📄";
    return "🖼️";
  };

  return (
    <div style={{ position: "relative" }}>
      <div
        className={`upload-zone ${isDragOver ? "drag-over" : ""} ${selectedFile ? "has-file" : ""}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClick}
        id="upload-zone"
        role="button"
        tabIndex={0}
        aria-label="Upload document"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.webp"
          onChange={handleInputChange}
          style={{ display: "none" }}
          id="file-input"
          disabled={isProcessing}
        />

        <div style={{ position: "relative", zIndex: 1 }}>
          {selectedFile ? (
            <div className="animate-slide-up" style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.75rem" }}>
              <span style={{ fontSize: "2.5rem" }}>{getFileIcon(selectedFile.type)}</span>
              <div>
                <p style={{
                  fontSize: "1.05rem",
                  fontWeight: 600,
                  color: "var(--foreground)",
                  margin: 0,
                }}>
                  {selectedFile.name}
                </p>
                <p style={{
                  fontSize: "0.85rem",
                  color: "var(--foreground-muted)",
                  margin: "0.25rem 0 0 0",
                }}>
                  {formatFileSize(selectedFile.size)} • Click or drop to replace
                </p>
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "1rem" }}>
              <div
                className="animate-float"
                style={{
                  fontSize: "3rem",
                  opacity: 0.7,
                }}
              >
                📤
              </div>
              <div>
                <p style={{
                  fontSize: "1.1rem",
                  fontWeight: 600,
                  color: "var(--foreground)",
                  margin: 0,
                }}>
                  Drop your document here
                </p>
                <p style={{
                  fontSize: "0.875rem",
                  color: "var(--foreground-muted)",
                  margin: "0.5rem 0 0 0",
                }}>
                  or click to browse • PDF, PNG, JPG, WEBP up to {MAX_SIZE_MB}MB
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div
          className="animate-slide-up"
          style={{
            marginTop: "0.75rem",
            padding: "0.625rem 1rem",
            background: "var(--color-error-bg)",
            border: "1px solid rgba(248, 113, 113, 0.2)",
            borderRadius: "var(--radius-sm)",
            color: "var(--color-error)",
            fontSize: "0.85rem",
          }}
          id="upload-error"
        >
          ⚠️ {error}
        </div>
      )}
    </div>
  );
}
