"""
TRAINING MATERIAL: Security Domain ML Models Package
====================================================

This package contains 4 ML models for the Security Agent domain,
all using **unsupervised anomaly detection** due to the nature of security threats.

SECURITY DOMAIN MODEL INVENTORY:
--------------------------------

┌────────────────────────────────────────────────────────────────────────────┐
│  MODEL                       │  ALGORITHM       │  DETECTS                  │
├──────────────────────────────┼──────────────────┼───────────────────────────┤
│  security_threat_detector    │  Isolation Forest│  General security threats │
│  exfiltration_detector       │  Isolation Forest│  Data theft patterns      │
│  privilege_escalation_detector│ Isolation Forest│  Permission abuse         │
│  user_behavior_baseline      │  Isolation Forest│  Per-user anomalies       │
└──────────────────────────────┴──────────────────┴───────────────────────────┘

WHY ALL ISOLATION FOREST:
-------------------------

Security threats are fundamentally rare events with no reliable labels.

┌─────────────────────────────────────────────────────────────────────────┐
│  CHALLENGE                  │  WHY UNSUPERVISED WORKS                   │
├─────────────────────────────┼───────────────────────────────────────────┤
│  Attacks are rare           │  No need for balanced labeled data        │
│  New attack types emerge    │  Detects ANY deviation, not just known    │
│  Labeling is expensive      │  No security analyst review needed        │
│  Zero-day detection needed  │  Learns "normal", flags deviations        │
└─────────────────────────────┴───────────────────────────────────────────┘

FEATURE TABLE: security_features
--------------------------------

Primary Keys: workspace_id, event_date
Key Features:
- failed_login_count: Authentication failures
- sensitive_action_count: High-privilege operations
- unique_resource_count: Resources accessed
- after_hours_activity_rate: Off-hours actions
- permission_change_count: Permission modifications

CONTAMINATION TUNING:
---------------------

Security models use lower contamination (0.05-0.1) than other domains
because security threats are rarer than cost anomalies.

    # Security: More conservative
    model = IsolationForest(contamination=0.05)
    
    # Cost: Higher anomaly rate expected
    model = IsolationForest(contamination=0.1)

4 Models: Threat Detector, Exfiltration Detector, Privilege Escalation Detector, User Behavior Baseline
"""






