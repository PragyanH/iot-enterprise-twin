# Aegis detection policy

`aegis_rules.yaml` contains executable, validated known-attack rules. A matched rule is authoritative evidence for a known attack.

`mitre_scenarios.yaml` contains exactly eight presentation scenarios and their honest provenance modes. It is a demo catalog, not eight executable signatures: scenarios marked `simulation_poc` normally exercise the unknown-behavior path and remain MITRE-unmapped in the model classification itself.
