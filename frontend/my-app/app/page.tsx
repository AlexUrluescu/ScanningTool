"use client";

import OnboardingFormSec from "@/components/OnboardingFormSec";

export default function Home() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        background:
          "linear-gradient(180deg, var(--background) 0%, var(--background-secondary) 50%, var(--background) 100%)",
      }}
    >
      <header
        style={{
          padding: "2rem 2rem 0",
          maxWidth: "1400px",
          width: "100%",
          margin: "0 auto",
        }}
      ></header>

      <main
        style={{
          flex: 1,
          maxWidth: "1400px",
          width: "100%",
          margin: "0 auto",
          padding: "0 2rem 3rem",
        }}
      >
        <OnboardingFormSec />
      </main>
    </div>
  );
}
