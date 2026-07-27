"use client";

import React, { useEffect, useState } from "react";

interface ProcessingIndicatorProps {
  isVisible: boolean;
}

const STEPS = [
  { label: "Parsing document", key: "parse" },
  { label: "Analyzing content", key: "analyze" },
  { label: "Extracting data", key: "extract" },
];

export default function ProcessingIndicator({ isVisible }: ProcessingIndicatorProps) {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (!isVisible) {
      setActiveStep(0);
      return;
    }

    const interval = setInterval(() => {
      setActiveStep((prev) => {
        if (prev < STEPS.length - 1) return prev + 1;
        return prev;
      });
    }, 2500);

    return () => clearInterval(interval);
  }, [isVisible]);

  if (!isVisible) return null;

  return (
    <div className="glass-card animate-slide-up processing-container" id="processing-indicator">
      <div className="processing-spinner" />
      <p className="processing-label">AI is analyzing your document...</p>

      <div className="processing-steps">
        {STEPS.map((step, i) => {
          let status = "";
          if (i < activeStep) status = "completed";
          else if (i === activeStep) status = "active";

          return (
            <div key={step.key} className={`processing-step ${status}`}>
              <span className="step-dot" />
              <span>
                {status === "completed" ? "✓ " : ""}
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
