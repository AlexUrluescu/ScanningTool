"use client";

import React, { useState, useCallback, useRef } from "react";
import BusinessTripForm, { ExpenseData } from "./BusinessTripForm";

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
  const [expenses, setExpenses] = useState<ExpenseData[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFilesSelected = useCallback(
    async (newFiles: FileList | File[]) => {
      const items: FileItem[] = [];
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
      if (items.length === 0) return;

      setFiles(items);
      setError(null);

      // Automatically process when files are added
      setIsProcessing(true);
      try {
        const formData = new FormData();
        items.forEach((f) => formData.append("files", f.file));

        const response = await fetch(`${API_URL}/api/report`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const err = await response.json().catch(() => null);
          throw new Error(err?.detail || `Server error: ${response.status}`);
        }

        const result = await response.json();

        console.log("result", result);

        if (result.success === false) {
          throw new Error(
            result.error || "The document could not be processed.",
          );
        }

        const newExpense = result.expenses;

        if (
          items.length === 1 &&
          newExpense &&
          Object.keys(newExpense).length > 0
        ) {
          newExpense.filename = items[0].file.name;
          setExpenses((prev) => [...prev, newExpense]);
        } else if (newExpense && Object.keys(newExpense).length > 0) {
          setExpenses((prev) => [...prev, newExpense]);
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "An unexpected error occurred",
        );
      } finally {
        setIsProcessing(false);
      }
    },
    [],
  );

  return (
    <div style={{ margin: "-2rem -2rem -3rem", height: "100vh" }}>
      {isProcessing && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.7)",
            zIndex: 9999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
            color: "white",
          }}
        >
          <div
            className="processing-spinner"
            style={{ marginBottom: "1rem" }}
          />
          <p>Analyzing document with AI...</p>
        </div>
      )}

      {error && (
        <div
          style={{
            position: "fixed",
            top: "20px",
            left: "20px",
            right: "20px",
            padding: "1rem",
            background: "#ff453a",
            color: "white",
            borderRadius: "8px",
            zIndex: 10000,
          }}
        >
          {error}
          <button
            onClick={() => setError(null)}
            style={{
              float: "right",
              background: "none",
              border: "none",
              color: "white",
              cursor: "pointer",
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Hidden file input for the form to trigger */}
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

      <div
        onClick={(e) => {
          // Intercept clicks on the "Upload document" button in the form
          const target = e.target as HTMLElement;
          if (
            target.textContent === "Upload document" ||
            target.closest("div")?.textContent?.includes("Upload document")
          ) {
            fileInputRef.current?.click();
          }
        }}
      >
        <BusinessTripForm
          expenses={
            expenses.length > 0
              ? expenses
              : [
                  {
                    expense_description: "",
                    invoice_number_date: "",
                    expense_amount: 0,
                    currency: "RON",
                  },
                ]
          }
          onExpensesChange={setExpenses}
        />
      </div>
    </div>
  );
}
