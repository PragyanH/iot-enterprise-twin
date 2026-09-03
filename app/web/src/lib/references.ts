export type Reference = { organization: string; title: string; description: string; url: string };

// Replace empty URLs only after the team verifies the exact source pages.
export const references: Record<"ibm" | "kyndryl" | "ecosystem", Reference> = {
  ibm: { organization: "IBM", title: "Enterprise Resiliency Architecture", description: "Reference for enterprise-scale cyber resiliency principles.", url: "" },
  kyndryl: { organization: "Kyndryl", title: "Cyber Resilience by Design", description: "Reference for the anticipate, protect, withstand, recover framework.", url: "" },
  ecosystem: { organization: "Source pending", title: "Ecosystem-level security reference", description: "Add a verified source that supports the ecosystem security framing.", url: "" }
};
