"use client";

import React from "react";

export interface EducationItem {
  institution: string;
  degree: string;
  years: string;
}

export interface ExperienceItem {
  company: string;
  role: string;
  years: string;
  description: string;
}

export interface CVData {
  name: string;
  email: string;
  phone: string;
  location: string;
  education: EducationItem[];
  experience: ExperienceItem[];
  skills: string[];
  languages: string[];
  error?: string;
}

interface CVResultsFormProps {
  data: CVData;
  onChange: (data: CVData) => void;
}

export default function CVResultsForm({ data, onChange }: CVResultsFormProps) {
  const updateField = (field: keyof CVData, value: any) => {
    onChange({ ...data, [field]: value });
  };

  const updateArrayItem = (arrayField: 'education' | 'experience', index: number, field: string, value: string) => {
    const newArray = [...data[arrayField]] as any[];
    newArray[index] = { ...newArray[index], [field]: value };
    onChange({ ...data, [arrayField]: newArray });
  };

  return (
    <div className="animate-slide-up" style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Error Banner */}
      {data.error && (
        <div
          style={{
            padding: "0.875rem 1rem",
            background: "var(--color-error-bg)",
            border: "1px solid rgba(248, 113, 113, 0.2)",
            borderRadius: "var(--radius-md)",
            color: "var(--color-error)",
            fontSize: "0.875rem",
          }}
          id="cv-extraction-error"
        >
          ⚠️ {data.error}
        </div>
      )}

      {/* Personal Information */}
      <div className="glass-card" style={{ padding: "1.5rem" }} id="section-personal">
        <div className="section-header">
          <div className="section-icon">👤</div>
          <h3 className="section-title">Personal Information</h3>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
          <div className="form-group">
            <label className="form-label" htmlFor="cv_name">Full Name</label>
            <input
              id="cv_name"
              className="form-input"
              value={data.name || ""}
              onChange={(e) => updateField("name", e.target.value)}
              placeholder="Candidate Name"
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="cv_email">Email</label>
            <input
              id="cv_email"
              className="form-input"
              type="email"
              value={data.email || ""}
              onChange={(e) => updateField("email", e.target.value)}
              placeholder="email@example.com"
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="cv_phone">Phone</label>
            <input
              id="cv_phone"
              className="form-input"
              value={data.phone || ""}
              onChange={(e) => updateField("phone", e.target.value)}
              placeholder="Phone number"
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="cv_location">Location</label>
            <input
              id="cv_location"
              className="form-input"
              value={data.location || ""}
              onChange={(e) => updateField("location", e.target.value)}
              placeholder="City, Country"
            />
          </div>
        </div>
      </div>

      {/* Experience */}
      {(data.experience && data.experience.length > 0) && (
        <div className="glass-card" style={{ padding: "1.5rem" }} id="section-experience">
          <div className="section-header">
            <div className="section-icon">💼</div>
            <h3 className="section-title">Experience</h3>
            <span className="badge badge-success">{data.experience.length} roles</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            {data.experience.map((exp, index) => (
              <div key={index} style={{ display: "flex", flexDirection: "column", gap: "0.75rem", paddingBottom: index < data.experience.length - 1 ? "1.5rem" : "0", borderBottom: index < data.experience.length - 1 ? "1px solid var(--border-color)" : "none" }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem" }}>
                  <div className="form-group">
                    <label className="form-label">Company</label>
                    <input
                      className="form-input"
                      value={exp.company || ""}
                      onChange={(e) => updateArrayItem("experience", index, "company", e.target.value)}
                      placeholder="Company Name"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Role</label>
                    <input
                      className="form-input"
                      value={exp.role || ""}
                      onChange={(e) => updateArrayItem("experience", index, "role", e.target.value)}
                      placeholder="Job Title"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Years</label>
                    <input
                      className="form-input"
                      value={exp.years || ""}
                      onChange={(e) => updateArrayItem("experience", index, "years", e.target.value)}
                      placeholder="e.g. 2020 - 2023"
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea
                    className="form-input"
                    value={exp.description || ""}
                    onChange={(e) => updateArrayItem("experience", index, "description", e.target.value)}
                    placeholder="Responsibilities and achievements..."
                    style={{ minHeight: "80px", resize: "vertical" }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Education */}
      {(data.education && data.education.length > 0) && (
        <div className="glass-card" style={{ padding: "1.5rem" }} id="section-education">
          <div className="section-header">
            <div className="section-icon">🎓</div>
            <h3 className="section-title">Education</h3>
            <span className="badge badge-success">{data.education.length} degrees</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {data.education.map((edu, index) => (
              <div key={index} style={{ display: "grid", gridTemplateColumns: "1.5fr 1.5fr 1fr", gap: "1rem" }}>
                <div className="form-group">
                  <label className="form-label">Institution</label>
                  <input
                    className="form-input"
                    value={edu.institution || ""}
                    onChange={(e) => updateArrayItem("education", index, "institution", e.target.value)}
                    placeholder="University Name"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Degree</label>
                  <input
                    className="form-input"
                    value={edu.degree || ""}
                    onChange={(e) => updateArrayItem("education", index, "degree", e.target.value)}
                    placeholder="Bachelor of Science"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Years</label>
                  <input
                    className="form-input"
                    value={edu.years || ""}
                    onChange={(e) => updateArrayItem("education", index, "years", e.target.value)}
                    placeholder="e.g. 2016 - 2020"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Skills & Languages */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
        <div className="glass-card" style={{ padding: "1.5rem" }} id="section-skills">
          <div className="section-header">
            <div className="section-icon">⚡</div>
            <h3 className="section-title">Skills</h3>
          </div>
          <div className="form-group">
            <textarea
              className="form-input"
              value={(data.skills || []).join(", ")}
              onChange={(e) => updateField("skills", e.target.value.split(",").map(s => s.trim()))}
              placeholder="React, Node.js, Python..."
              style={{ minHeight: "100px", resize: "vertical" }}
            />
          </div>
        </div>
        <div className="glass-card" style={{ padding: "1.5rem" }} id="section-languages">
          <div className="section-header">
            <div className="section-icon">🌍</div>
            <h3 className="section-title">Languages</h3>
          </div>
          <div className="form-group">
            <textarea
              className="form-input"
              value={(data.languages || []).join(", ")}
              onChange={(e) => updateField("languages", e.target.value.split(",").map(s => s.trim()))}
              placeholder="English, Romanian..."
              style={{ minHeight: "100px", resize: "vertical" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
