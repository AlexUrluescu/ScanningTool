"use client";

import React, { useState, useCallback, useRef, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface OnboardingData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  cnp: string;
  birthDate: string;
  address: string;
  city: string;
  postalCode: string;
  jobTitle: string;
  department: string;
  startDate: string;
  iban: string;
  emergencyContactName: string;
  emergencyContactPhone: string;
}

const EMPTY_DATA: OnboardingData = {
  firstName: "",
  lastName: "",
  email: "",
  phone: "",
  cnp: "",
  birthDate: "",
  address: "",
  city: "",
  postalCode: "",
  jobTitle: "",
  department: "",
  startDate: "",
  iban: "",
  emergencyContactName: "",
  emergencyContactPhone: "",
};

const FIELD_SECTIONS: {
  title: string;
  icon: string;
  fields: { key: keyof OnboardingData; label: string; type?: string }[];
}[] = [
  {
    title: "Personal Details",
    icon: "",
    fields: [
      { key: "firstName", label: "First Name" },
      { key: "lastName", label: "Last Name" },
      { key: "email", label: "Email", type: "email" },
      { key: "phone", label: "Phone", type: "tel" },
      { key: "cnp", label: "CNP" },
      { key: "birthDate", label: "Date of Birth", type: "date" },
    ],
  },
  {
    title: "Address",
    icon: "",
    fields: [
      { key: "address", label: "Address" },
      { key: "city", label: "City" },
      { key: "postalCode", label: "Postal Code" },
    ],
  },
  {
    title: "Employment Details",
    icon: "",
    fields: [
      { key: "jobTitle", label: "Job Title" },
      { key: "department", label: "Department" },
      { key: "startDate", label: "Start Date", type: "date" },
      { key: "iban", label: "IBAN" },
    ],
  },
  {
    title: "Emergency Contact",
    icon: "",
    fields: [
      { key: "emergencyContactName", label: "Contact Name" },
      { key: "emergencyContactPhone", label: "Contact Phone", type: "tel" },
    ],
  },
];

export default function OnboardingFormSec() {
  const [data, setData] = useState<OnboardingData>(EMPTY_DATA);
  const [isExtracting, setIsExtracting] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiFileName, setAiFileName] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [documentType, setDocumentType] = useState<string | null>(null);

  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewType, setPreviewType] = useState<"image" | "pdf" | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleFieldChange = useCallback(
    (key: keyof OnboardingData, value: string) => {
      setData((prev) => ({ ...prev, [key]: value }));
    },
    [],
  );

  const handleUseAiClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileSelected = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      if (previewUrl) URL.revokeObjectURL(previewUrl);
      const blobUrl = URL.createObjectURL(file);
      setPreviewUrl(blobUrl);
      setPreviewType(file.type === "application/pdf" ? "pdf" : "image");

      setAiFileName(file.name);
      setAiError(null);
      setIsExtracting(true);
      setDocumentType(null);

      try {
        const formData = new FormData();
        formData.append("file", file);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5 * 60 * 1000);

        const response = await fetch(`${API_URL}/api/extract`, {
          method: "POST",
          body: formData,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorData = await response.json().catch(() => null);
          throw new Error(
            errorData?.detail || `Server error: ${response.status}`,
          );
        }

        const result = await response.json();

        console.log("AI extraction result:", result);

        if (!result.success || !result.data) {
          throw new Error("Unexpected response format from server");
        }

        if (result.document_type) {
          setDocumentType(result.document_type);
        }

        setData((prev) => {
          const merged = { ...prev };
          (Object.keys(EMPTY_DATA) as (keyof OnboardingData)[]).forEach(
            (key) => {
              const value = result.data[key];
              if (value !== undefined && value !== null && value !== "") {
                merged[key] = String(value);
              }
            },
          );
          return merged;
        });
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "An unexpected error occurred";
        setAiError(message);
      } finally {
        setIsExtracting(false);
        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    },
    [previewUrl],
  );

  const handleReset = useCallback(() => {
    setData(EMPTY_DATA);
    setAiError(null);
    setAiFileName(null);
    setSubmitSuccess(false);
    setDocumentType(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setPreviewType(null);
  }, [previewUrl]);

  const hasPreview = previewUrl !== null;

  const docTypeLabels: Record<string, string> = {
    ID_CARD: "🪪 ID Card",
    CV: "📄 CV / Resume",
    CONTRACT: "📝 Contract",
    OTHER: "📎 Document",
    UNKNOWN: "📎 Document",
  };

  const previewPanel = hasPreview && (
    <div className="preview-panel glass-card">
      <div className="preview-header">
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            minWidth: 0,
          }}
        >
          <span style={{ fontSize: "1.1rem", flexShrink: 0 }}>
            {previewType === "pdf" ? "📄" : "🖼️"}
          </span>
          <span className="preview-filename">{aiFileName}</span>
        </div>
        {documentType && (
          <span className="badge badge-success">
            {docTypeLabels[documentType] || documentType}
          </span>
        )}
      </div>

      <div className="preview-content">
        {previewType === "pdf" ? (
          <object
            data={previewUrl}
            type="application/pdf"
            width="100%"
            height="450px"
            style={{ borderRadius: "var(--radius-sm)", background: "orange" }}
          >
            <p
              style={{
                padding: "2rem",
                textAlign: "center",
                color: "var(--foreground-muted)",
              }}
            >
              Your browser cannot display the PDF.{" "}
              <a
                href={previewUrl}
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: "var(--color-primary)" }}
              >
                Open in a new tab
              </a>
            </p>
          </object>
        ) : (
          <img
            src={previewUrl}
            alt="Document preview"
            className="preview-image"
          />
        )}
      </div>

      <button
        type="button"
        className="btn btn-ghost"
        onClick={handleUseAiClick}
        disabled={isExtracting}
        style={{ width: "100%", marginTop: "0.5rem", fontSize: "0.8rem" }}
      >
        Replace document
      </button>
    </div>
  );

  const formPanel = (
    <div className="form-panel">
      {!hasPreview && (
        <div
          className="glass-card"
          style={{
            padding: "1.25rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "1rem",
          }}
        >
          <div
            style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}
          >
            <span style={{ fontWeight: 600 }}>Auto-fill with AI</span>
            <span
              style={{ fontSize: "0.8rem", color: "var(--foreground-muted)" }}
            >
              Accepts PDF, JPG or PNG
            </span>
          </div>

          <button
            type="button"
            className="btn btn-primary"
            onClick={handleUseAiClick}
            disabled={isExtracting}
            style={{ minWidth: "160px" }}
          >
            {isExtracting ? "Processing…" : "Use AI"}
          </button>
        </div>
      )}

      {isExtracting && (
        <div
          className="glass-card animate-slide-up"
          style={{ padding: "1.5rem", textAlign: "center" }}
        >
          <div
            className="processing-spinner"
            style={{ margin: "0 auto 1rem" }}
          />
          <p className="processing-label">AI is analyzing your document…</p>
        </div>
      )}

      {aiError && (
        <div
          className="glass-card"
          style={{ padding: "1rem", borderColor: "rgba(248, 113, 113, 0.3)" }}
        >
          <p
            style={{ color: "var(--color-error)", margin: 0, fontWeight: 600 }}
          >
            {aiError}
          </p>
        </div>
      )}

      {submitSuccess && (
        <div
          className="glass-card"
          style={{ padding: "1rem", borderColor: "rgba(74, 222, 128, 0.3)" }}
        >
          <p style={{ margin: 0, fontWeight: 600 }}>
            ✓ Onboarding data submitted successfully.
          </p>
        </div>
      )}

      {FIELD_SECTIONS.map((section) => (
        <div
          key={section.title}
          className="glass-card"
          style={{ padding: "1.25rem" }}
        >
          <div className="section-header">
            <div className="section-icon">{section.icon}</div>
            <h2 className="section-title">{section.title}</h2>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "1rem",
            }}
          >
            {section.fields.map((field) => (
              <label key={field.key} className="form-group">
                <span className="form-label">{field.label}</span>
                <input
                  type={field.type || "text"}
                  className="form-input"
                  value={data[field.key]}
                  onChange={(e) => handleFieldChange(field.key, e.target.value)}
                />
              </label>
            ))}
          </div>
        </div>
      ))}

      <div
        style={{ display: "flex", gap: "0.75rem", justifyContent: "center" }}
      >
        <button className="btn btn-primary">Continue</button>
        <button type="button" className="btn btn-ghost" onClick={handleReset}>
          Reset
        </button>
      </div>
    </div>
  );

  const hiddenInput = (
    <input
      ref={fileInputRef}
      type="file"
      accept=".pdf,image/*"
      onChange={handleFileSelected}
      style={{ display: "none" }}
    />
  );

  return (
    <div style={{ width: "100%", padding: "2rem 1.5rem 3rem" }}>
      {hiddenInput}

      <div
        style={{
          textAlign: "center",
          marginBottom: "1.5rem",
          maxWidth: "760px",
          margin: "0 auto 1.5rem",
        }}
      >
        <h1
          style={{
            fontSize: "1.6rem",
            fontWeight: 700,
            margin: "0 0 0.5rem 0",
            background:
              "linear-gradient(135deg, var(--foreground) 0%, var(--color-primary) 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          New Employee Onboarding
        </h1>
        <p
          style={{
            color: "var(--foreground-secondary)",
            margin: 0,
            fontSize: "0.95rem",
          }}
        >
          Fill in manually, or upload a document (ID card, contract, CV) and
          let the AI auto-fill the fields for you.
        </p>
      </div>

      <div className={hasPreview ? "split-layout" : "single-layout"}>
        {previewPanel}
        {formPanel}
      </div>
    </div>
  );
}
