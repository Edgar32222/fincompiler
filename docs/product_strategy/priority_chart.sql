WITH priorities(problem, decision_score, next_capability) AS (
  SELECT 'Complex reconciliation', 5, 'Many-to-many matching and cut-off reasoning'
  UNION ALL SELECT 'Exception resolution', 4, 'Owner, status, evidence and maker-checker'
  UNION ALL SELECT 'Finance deliverables', 3, 'Excel pack and exception workbook'
  UNION ALL SELECT 'Guided setup', 2, 'Company and period onboarding'
  UNION ALL SELECT 'Pilot evidence', 1, 'Task telemetry and repeated close measurement'
)
SELECT problem, decision_score, next_capability
FROM priorities
ORDER BY decision_score DESC;
