"use client";

import { useEffect, useState } from "react";

export function ResearchPaperModal({ onClose }: { onClose: () => void }) {
  const [paperText, setPaperText] = useState<string>("Loading research paper...");

  useEffect(() => {
    fetch("/aegis_twin_research_paper.md")
      .then((res) => res.text())
      .then((text) => setPaperText(text))
      .catch(() => setPaperText("Failed to load paper content."));
  }, []);

  const handleDownload = () => {
    const element = document.createElement("a");
    const file = new Blob([paperText], { type: "text/markdown" });
    element.href = URL.createObjectURL(file);
    element.download = "AEGIS-TWIN_Research_Paper_2026.md";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="module-modal" role="dialog" aria-modal="true" aria-label="Aegis-Twin Research Paper">
      <div className="module-modal-content" style={{ maxWidth: "900px", width: "90vw", maxHeight: "88vh", padding: "28px" }}>
        <button
          type="button"
          className="module-modal-close"
          onClick={onClose}
          aria-label="Close modal"
          style={{ position: "absolute", top: "18px", right: "18px" }}
        >
          ×
        </button>

        {/* Paper Header & Download Bar */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--line)", paddingBottom: "16px", marginBottom: "20px" }}>
          <div>
            <span className="eyebrow" style={{ color: "var(--cyan)" }}>HACKATHON RESEARCH PROTOTYPE — 2026</span>
            <h2 style={{ margin: "4px 0 0", fontSize: "20px", color: "var(--ink)" }}>AEGIS-TWIN Research Paper</h2>
          </div>
          <button
            type="button"
            className="attack-button"
            onClick={handleDownload}
            style={{
              background: "var(--cyan)",
              color: "#000",
              borderColor: "var(--cyan)",
              fontWeight: "700",
              padding: "10px 18px",
              fontSize: "12px",
              cursor: "pointer",
              borderRadius: "4px",
              boxShadow: "0 4px 14px color-mix(in srgb, var(--cyan) 30%, transparent)",
            }}
          >
            📥 DOWNLOAD PAPER (.MD / PDF)
          </button>
        </div>

        {/* Paper Content Display Area */}
        <div
          style={{
            maxHeight: "calc(88vh - 140px)",
            overflowY: "auto",
            background: "var(--color-surface-raised)",
            border: "1px solid var(--line)",
            padding: "24px",
            borderRadius: "4px",
            fontFamily: "Arial, sans-serif",
            fontSize: "13px",
            lineHeight: "1.6",
            color: "var(--ink)",
            whiteSpace: "pre-wrap",
          }}
        >
          {paperText}
        </div>
      </div>
    </div>
  );
}
