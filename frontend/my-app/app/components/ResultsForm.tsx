"use client";

import React from "react";

export interface LineItem {
  description: string;
  quantity: number | null;
  unit_price: number | null;
  amount: number | null;
}

export interface InvoiceData {
  vendor_name: string;
  vendor_address: string;
  invoice_number: string;
  date: string;
  due_date: string;
  subtotal: number | null;
  tax: number | null;
  total: number | null;
  currency: string;
  items: LineItem[];
  payment_method: string;
  notes: string;
  error?: string;
}

interface ResultsFormProps {
  data: InvoiceData;
  onChange: (data: InvoiceData) => void;
}

export default function ResultsForm({ data, onChange }: ResultsFormProps) {
  const updateField = (field: keyof InvoiceData, value: string | number | null) => {
    onChange({ ...data, [field]: value });
  };

  const updateItem = (index: number, field: keyof LineItem, value: string | number | null) => {
    const newItems = [...data.items];
    newItems[index] = { ...newItems[index], [field]: value };
    onChange({ ...data, items: newItems });
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
          id="extraction-error"
        >
          ⚠️ {data.error}
        </div>
      )}

      {/* Vendor Information */}
      <div className="glass-card" style={{ padding: "1.5rem" }} id="section-vendor">
        <div className="section-header">
          <div className="section-icon">🏢</div>
          <h3 className="section-title">Vendor Information</h3>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
          <div className="form-group">
            <label className="form-label" htmlFor="vendor_name">Vendor Name</label>
            <input
              id="vendor_name"
              className="form-input"
              value={data.vendor_name}
              onChange={(e) => updateField("vendor_name", e.target.value)}
              placeholder="Company name"
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="vendor_address">Address</label>
            <input
              id="vendor_address"
              className="form-input"
              value={data.vendor_address}
              onChange={(e) => updateField("vendor_address", e.target.value)}
              placeholder="Vendor address"
            />
          </div>
        </div>
      </div>

      {/* Invoice Details */}
      <div className="glass-card" style={{ padding: "1.5rem" }} id="section-details">
        <div className="section-header">
          <div className="section-icon">📋</div>
          <h3 className="section-title">Invoice Details</h3>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem" }}>
          <div className="form-group">
            <label className="form-label" htmlFor="invoice_number">Invoice Number</label>
            <input
              id="invoice_number"
              className="form-input"
              value={data.invoice_number}
              onChange={(e) => updateField("invoice_number", e.target.value)}
              placeholder="INV-001"
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="date">Date</label>
            <input
              id="date"
              className="form-input"
              value={data.date}
              onChange={(e) => updateField("date", e.target.value)}
              placeholder="YYYY-MM-DD"
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="due_date">Due Date</label>
            <input
              id="due_date"
              className="form-input"
              value={data.due_date}
              onChange={(e) => updateField("due_date", e.target.value)}
              placeholder="YYYY-MM-DD"
            />
          </div>
        </div>
      </div>

      {/* Line Items */}
      {data.items.length > 0 && (
        <div className="glass-card" style={{ padding: "1.5rem" }} id="section-items">
          <div className="section-header">
            <div className="section-icon">📦</div>
            <h3 className="section-title">Line Items</h3>
            <span className="badge badge-success">{data.items.length} items</span>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table className="items-table">
              <thead>
                <tr>
                  <th style={{ minWidth: "200px" }}>Description</th>
                  <th style={{ width: "100px" }}>Qty</th>
                  <th style={{ width: "120px" }}>Unit Price</th>
                  <th style={{ width: "120px" }}>Amount</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item, index) => (
                  <tr key={index}>
                    <td>
                      <input
                        className="form-input"
                        value={item.description}
                        onChange={(e) => updateItem(index, "description", e.target.value)}
                        style={{ padding: "0.375rem 0.625rem" }}
                      />
                    </td>
                    <td>
                      <input
                        className="form-input"
                        type="number"
                        value={item.quantity ?? ""}
                        onChange={(e) => updateItem(index, "quantity", e.target.value ? parseFloat(e.target.value) : null)}
                        style={{ padding: "0.375rem 0.625rem" }}
                      />
                    </td>
                    <td>
                      <input
                        className="form-input"
                        type="number"
                        step="0.01"
                        value={item.unit_price ?? ""}
                        onChange={(e) => updateItem(index, "unit_price", e.target.value ? parseFloat(e.target.value) : null)}
                        style={{ padding: "0.375rem 0.625rem" }}
                      />
                    </td>
                    <td>
                      <input
                        className="form-input"
                        type="number"
                        step="0.01"
                        value={item.amount ?? ""}
                        onChange={(e) => updateItem(index, "amount", e.target.value ? parseFloat(e.target.value) : null)}
                        style={{ padding: "0.375rem 0.625rem" }}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Financial Summary */}
      <div className="glass-card" style={{ padding: "1.5rem" }} id="section-financials">
        <div className="section-header">
          <div className="section-icon">💰</div>
          <h3 className="section-title">Financial Summary</h3>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "1rem" }}>
          <div className="form-group">
            <label className="form-label" htmlFor="subtotal">Subtotal</label>
            <input
              id="subtotal"
              className="form-input"
              type="number"
              step="0.01"
              value={data.subtotal ?? ""}
              onChange={(e) => updateField("subtotal", e.target.value ? parseFloat(e.target.value) : null)}
              placeholder="0.00"
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="tax">Tax</label>
            <input
              id="tax"
              className="form-input"
              type="number"
              step="0.01"
              value={data.tax ?? ""}
              onChange={(e) => updateField("tax", e.target.value ? parseFloat(e.target.value) : null)}
              placeholder="0.00"
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="total">Total</label>
            <input
              id="total"
              className="form-input"
              type="number"
              step="0.01"
              value={data.total ?? ""}
              onChange={(e) => updateField("total", e.target.value ? parseFloat(e.target.value) : null)}
              placeholder="0.00"
              style={{
                fontWeight: 700,
                fontSize: "1.05rem",
                color: "var(--color-success)",
              }}
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="currency">Currency</label>
            <input
              id="currency"
              className="form-input"
              value={data.currency}
              onChange={(e) => updateField("currency", e.target.value)}
              placeholder="USD"
            />
          </div>
        </div>
      </div>

      {/* Additional Info */}
      <div className="glass-card" style={{ padding: "1.5rem" }} id="section-additional">
        <div className="section-header">
          <div className="section-icon">📝</div>
          <h3 className="section-title">Additional Information</h3>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
          <div className="form-group">
            <label className="form-label" htmlFor="payment_method">Payment Method</label>
            <input
              id="payment_method"
              className="form-input"
              value={data.payment_method}
              onChange={(e) => updateField("payment_method", e.target.value)}
              placeholder="Credit card, bank transfer, etc."
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="notes">Notes</label>
            <input
              id="notes"
              className="form-input"
              value={data.notes}
              onChange={(e) => updateField("notes", e.target.value)}
              placeholder="Additional notes"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
