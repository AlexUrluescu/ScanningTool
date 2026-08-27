"use client";

import React from "react";

export interface ExpenseData {
  expense_description: string;
  invoice_number_date: string;
  expense_amount: number;
  currency: string;
  payment_method: string;
  filename?: string;
}

interface BusinessTripFormProps {
  expenses: ExpenseData[];
  onExpensesChange: (expenses: ExpenseData[]) => void;
}

export default function BusinessTripForm({
  expenses,
  onExpensesChange,
}: BusinessTripFormProps) {
  const updateExpense = (index: number, field: keyof ExpenseData, value: any) => {
    const newExpenses = [...expenses];
    newExpenses[index] = { ...newExpenses[index], [field]: value };
    onExpensesChange(newExpenses);
  };

  const removeExpense = (index: number) => {
    const newExpenses = [...expenses];
    newExpenses.splice(index, 1);
    onExpensesChange(newExpenses);
  };

  const addExpense = () => {
    onExpensesChange([
      ...expenses,
      {
        expense_description: "",
        invoice_number_date: "",
        expense_amount: 0,
        currency: "RON",
        payment_method: "",
      },
    ]);
  };

  const totalAmount = expenses.reduce((sum, e) => sum + (Number(e.expense_amount) || 0), 0);

  return (
    <div
      className="business-trip-container"
      style={{
        background: "#1c1c1e",
        color: "#fff",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
      }}
    >
      {/* Header */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          padding: "1rem",
          background: "#000",
          borderBottom: "1px solid #333",
        }}
      >
        <button
          style={{
            background: "#2c2c2e",
            border: "none",
            borderRadius: "50%",
            width: "36px",
            height: "36px",
            color: "#fff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
          }}
        >
          <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 style={{ flex: 1, textAlign: "center", fontSize: "1.1rem", margin: 0, fontWeight: 600 }}>
          Business Trip Report
        </h1>
        <div style={{ width: "36px" }} /> {/* Spacer for centering */}
      </header>

      {/* Main Content */}
      <main style={{ flex: 1, padding: "1rem" }}>
        {/* Transport Costs Section */}
        <section style={{ marginBottom: "2rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 600, margin: 0 }}>Transport costs</h2>
            <span style={{ fontSize: "0.9rem", color: "#e0e0e0" }}>{totalAmount.toFixed(2)} RON</span>
          </div>
          <p style={{ fontSize: "0.8rem", color: "#8e8e93", margin: "0 0 1rem 0" }}>
            Includes transport costs only.
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {expenses.map((expense, index) => (
              <div
                key={index}
                style={{
                  background: "#2c2c2e",
                  borderRadius: "12px",
                  padding: "1rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "1rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <h3 style={{ fontSize: "0.9rem", margin: 0, fontWeight: 600 }}>Transport Expense {index + 1}</h3>
                  <button
                    onClick={() => removeExpense(index)}
                    style={{ background: "none", border: "none", color: "#8e8e93", cursor: "pointer", fontSize: "1.2rem" }}
                  >
                    ×
                  </button>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  <label style={{ fontSize: "0.85rem", fontWeight: 500 }}>Expense description</label>
                  <input
                    style={{
                      background: "#3a3a3c",
                      border: "none",
                      borderRadius: "8px",
                      padding: "0.75rem",
                      color: "#fff",
                      fontSize: "0.9rem",
                    }}
                    value={expense.expense_description || ""}
                    onChange={(e) => updateExpense(index, "expense_description", e.target.value)}
                    placeholder="Enter expense description"
                  />
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  <label style={{ fontSize: "0.85rem", fontWeight: 500 }}>Number and/date of invoice</label>
                  <input
                    style={{
                      background: "#3a3a3c",
                      border: "none",
                      borderRadius: "8px",
                      padding: "0.75rem",
                      color: "#fff",
                      fontSize: "0.9rem",
                    }}
                    value={expense.invoice_number_date || ""}
                    onChange={(e) => updateExpense(index, "invoice_number_date", e.target.value)}
                    placeholder="Enter number and/date of invoice"
                  />
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  <label style={{ fontSize: "0.85rem", fontWeight: 500 }}>Expense amount</label>
                  <input
                    type="number"
                    style={{
                      background: "#3a3a3c",
                      border: "none",
                      borderRadius: "8px",
                      padding: "0.75rem",
                      color: "#fff",
                      fontSize: "0.9rem",
                    }}
                    value={expense.expense_amount || ""}
                    onChange={(e) => updateExpense(index, "expense_amount", parseFloat(e.target.value) || 0)}
                  />
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  <label style={{ fontSize: "0.85rem", fontWeight: 500 }}>Currency</label>
                  <select
                    style={{
                      background: "#3a3a3c",
                      border: "none",
                      borderRadius: "8px",
                      padding: "0.75rem",
                      color: "#fff",
                      fontSize: "0.9rem",
                      appearance: "none",
                    }}
                    value={expense.currency || "RON"}
                    onChange={(e) => updateExpense(index, "currency", e.target.value)}
                  >
                    <option value="RON">RON</option>
                    <option value="EUR">EUR</option>
                    <option value="USD">USD</option>
                  </select>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  <label style={{ fontSize: "0.85rem", fontWeight: 500 }}>Payment method</label>
                  <select
                    style={{
                      background: "#3a3a3c",
                      border: "none",
                      borderRadius: "8px",
                      padding: "0.75rem",
                      color: "#fff",
                      fontSize: "0.9rem",
                      appearance: "none",
                    }}
                    value={expense.payment_method || ""}
                    onChange={(e) => updateExpense(index, "payment_method", e.target.value)}
                  >
                    <option value="" disabled>Select payment method</option>
                    <option value="Card">Card</option>
                    <option value="Cash">Cash</option>
                  </select>
                </div>

                <div
                  style={{
                    border: "1px dashed #4a4a4c",
                    borderRadius: "8px",
                    padding: "1rem",
                    textAlign: "center",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "0.5rem",
                    color: "#0a84ff",
                    marginTop: "0.5rem"
                  }}
                >
                  <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  <span>Upload document</span>
                </div>
                
                {expense.filename && (
                   <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.8rem", color: "#0a84ff", marginTop: "-0.5rem" }}>
                     <span style={{flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap"}}>{expense.filename}</span>
                     <div style={{background: "#ff453a", color: "white", borderRadius: "50%", width: "16px", height: "16px", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer"}}>
                        <span style={{marginTop: "-2px"}}>-</span>
                     </div>
                   </div>
                )}
              </div>
            ))}

            <button
              onClick={addExpense}
              style={{
                background: "transparent",
                border: "1px solid #4a4a4c",
                borderRadius: "24px",
                padding: "0.75rem",
                color: "#0a84ff",
                fontSize: "0.95rem",
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              Add expense
            </button>
          </div>
        </section>

        {/* Accommodation Section */}
        <section style={{ marginBottom: "2rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 600, margin: 0 }}>Accommodation costs</h2>
            <span style={{ fontSize: "0.9rem", color: "#e0e0e0" }}>0.00 RON</span>
          </div>
          <p style={{ fontSize: "0.8rem", color: "#8e8e93", margin: "0 0 1rem 0" }}>
            Includes hotel, Airbnb or special request lodging.
          </p>
        </section>
      </main>

      {/* Bottom Nav */}
      <footer
        style={{
          display: "flex",
          justifyContent: "space-around",
          alignItems: "center",
          padding: "0.75rem 1rem 2rem",
          background: "#000",
          borderTop: "1px solid #333",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.25rem", color: "#0a84ff", cursor: "pointer", background: "#1c1c1e", padding: "0.5rem 1.5rem", borderRadius: "24px" }}>
          <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
            <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" />
          </svg>
          <span style={{ fontSize: "0.7rem", fontWeight: 500 }}>Home</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.25rem", color: "#8e8e93", cursor: "pointer" }}>
          <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
          </svg>
          <span style={{ fontSize: "0.7rem", fontWeight: 500 }}>Archive</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.25rem", color: "#8e8e93", cursor: "pointer" }}>
          <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <span style={{ fontSize: "0.7rem", fontWeight: 500 }}>Profile</span>
        </div>
      </footer>
    </div>
  );
}
