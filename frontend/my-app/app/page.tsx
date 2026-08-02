"use client";

import FinancialReport from "@/components/FinancialReport";

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
      <main
        style={{
          flex: 1,
          width: "100%",
          margin: "0 auto",
          padding: "2rem 2rem 3rem",
        }}
      >
        <FinancialReport />
      </main>
    </div>
  );
}
