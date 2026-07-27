"use client";

import React, { useState, useCallback, useRef } from "react";

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
  fields: { key: keyof OnboardingData; label: string; type?: string }[];
}[] = [
  {
    title: "Date personale",
    fields: [
      { key: "firstName", label: "Prenume" },
      { key: "lastName", label: "Nume" },
      { key: "email", label: "Email", type: "email" },
      { key: "phone", label: "Telefon", type: "tel" },
      { key: "cnp", label: "CNP" },
      { key: "birthDate", label: "Data nașterii", type: "date" },
    ],
  },
  {
    title: "Adresă",
    fields: [
      { key: "address", label: "Adresă" },
      { key: "city", label: "Oraș" },
      { key: "postalCode", label: "Cod poștal" },
    ],
  },
  {
    title: "Date angajare",
    fields: [
      { key: "jobTitle", label: "Funcție" },
      { key: "department", label: "Departament" },
      { key: "startDate", label: "Data angajării", type: "date" },
      { key: "iban", label: "IBAN" },
    ],
  },
  {
    title: "Contact de urgență",
    fields: [
      { key: "emergencyContactName", label: "Nume contact" },
      { key: "emergencyContactPhone", label: "Telefon contact", type: "tel" },
    ],
  },
];

export default function OnboardingFormSec() {
  const [data, setData] = useState<OnboardingData>(EMPTY_DATA);
  const [isExtracting, setIsExtracting] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiFileName, setAiFileName] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

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

      setAiFileName(file.name);
      setAiError(null);
      setIsExtracting(true);

      try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(`${API_URL}/api/extract`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => null);
          throw new Error(
            errorData?.detail || `Server error: ${response.status}`,
          );
        }

        const result = await response.json();

        if (!result.success || !result.data) {
          throw new Error("Format de răspuns neașteptat de la server");
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
          err instanceof Error ? err.message : "A apărut o eroare neașteptată";
        setAiError(message);
      } finally {
        setIsExtracting(false);

        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    },
    [],
  );

  const handleReset = useCallback(() => {
    setData(EMPTY_DATA);
    setAiError(null);
    setAiFileName(null);
    setSubmitSuccess(false);
  }, []);

  return (
    <div
      style={{
        maxWidth: "760px",
        width: "100%",
        margin: "0 auto",
        padding: "2rem 1.5rem 3rem",
        display: "flex",
        flexDirection: "column",
        gap: "1.5rem",
      }}
    >
      <div style={{ textAlign: "center" }}>
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
          Onboarding angajat nou
        </h1>
        <p
          style={{
            color: "var(--foreground-secondary)",
            margin: 0,
            fontSize: "0.95rem",
          }}
        >
          Completează manual, sau atașează un document (CI, contract, CV) și
          lasă AI-ul să completeze câmpurile pentru tine.
        </p>
      </div>

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
          <span style={{ fontWeight: 600 }}>🤖 Completează automat cu AI</span>
          <span
            style={{ fontSize: "0.8rem", color: "var(--foreground-muted)" }}
          >
            {aiFileName
              ? `Ultimul fișier folosit: ${aiFileName}`
              : "Acceptă PDF, JPG sau PNG"}
          </span>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,image/*"
          onChange={handleFileSelected}
          style={{ display: "none" }}
        />

        <button
          type="button"
          className="btn btn-primary"
          onClick={handleUseAiClick}
          disabled={isExtracting}
          style={{ minWidth: "160px" }}
        >
          {isExtracting ? "Se procesează…" : "✨ Use AI"}
        </button>
      </div>

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
            ✓ Datele de onboarding au fost trimise cu succes.
          </p>
        </div>
      )}

      {FIELD_SECTIONS.map((section) => (
        <div
          key={section.title}
          className="glass-card"
          style={{ padding: "1.25rem" }}
        >
          <h2
            style={{
              fontSize: "1rem",
              fontWeight: 600,
              margin: "0 0 1rem 0",
              color: "var(--foreground)",
            }}
          >
            {section.title}
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "1rem",
            }}
          >
            {section.fields.map((field) => (
              <label
                key={field.key}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.35rem",
                }}
              >
                <span
                  style={{
                    fontSize: "0.8rem",
                    color: "var(--foreground-secondary)",
                  }}
                >
                  {field.label}
                </span>
                <input
                  type={field.type || "text"}
                  value={data[field.key]}
                  onChange={(e) => handleFieldChange(field.key, e.target.value)}
                  style={{
                    padding: "0.6rem 0.75rem",
                    borderRadius: "8px",
                    border: "1px solid var(--border-color)",
                    background: "var(--background)",
                    color: "var(--foreground)",
                    fontSize: "0.9rem",
                  }}
                />
              </label>
            ))}
          </div>
        </div>
      ))}

      <div
        style={{ display: "flex", gap: "0.75rem", justifyContent: "center" }}
      >
        <button type="button" className="btn btn-ghost" onClick={handleReset}>
          Resetează
        </button>
      </div>
    </div>
  );
}
