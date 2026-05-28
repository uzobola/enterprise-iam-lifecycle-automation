# IAM Lifecycle Architecture

## Architecture Overview

This project implements an HR-driven identity lifecycle workflow using SimplifyHR as the authoritative identity source, midPoint as the identity governance and reconciliation platform, and OpenLDAP as the downstream directory target.

```text
+---------------------------+
| SimplifyHR / HR CSV       |
| Authoritative Source      |
| - empid                   |
| - firstname               |
| - lastname                |
| - department              |
| - costcenter              |
| - status                  |
+-------------+-------------+
              |
              | Inbound mappings
              | Correlation on stable identifier
              v
+-------------+-------------+
| midPoint IGA Platform     |
| Governance Control Plane  |
| - Focus objects           |
| - Attribute mappings      |
| - Correlation rules       |
| - Reconciliation tasks    |
| - Role construction       |
| - Lifecycle logic         |
+-------------+-------------+
              |
              | Outbound mappings
              | Role-based provisioning
              v
+-------------+-------------+
| OpenLDAP / 389 DS         |
| Downstream Directory      |
| - uid                     |
| - cn                      |
| - givenName               |
| - sn                      |
| - mail                    |
| - employeeNumber          |
| - departmentNumber        |
+-------------+-------------+
              |
              | Verification + reconciliation
              v
+-------------+-------------+
| Audit Evidence            |
| - Object add events       |
| - Object modify events    |
| - Reconciliation results  |
| - Joiner evidence         |
| - Leaver evidence         |
| - Unmatched account risk  |
+---------------------------+
````

## Joiner Architecture Pattern

```text
New employee created in HR source
        |
        v
HR reconciliation task runs in midPoint
        |
        v
midPoint identifies new HR record
        |
        v
Focus object created in midPoint
        |
        v
Employee role assigned
        |
        v
Role construction triggers OpenLDAP account provisioning
        |
        v
LDAP account appears in ou=people
        |
        v
Audit trail records lifecycle event
```

## Leaver Architecture Pattern

```text
Employee marked Terminated in HR source
        |
        v
HR reconciliation task runs in midPoint
        |
        v
midPoint detects lifecycle status change
        |
        v
midPoint identity is disabled
        |
        v
Downstream LDAP account is removed from active access in project configuration
        |
        v
Audit trail records lifecycle event
```

## Production Leaver Design Recommendation

In a production enterprise design, the preferred pattern is usually:

```text
Terminate in HR
   -> Disable governed identity
   -> Disable / lock target accounts
   -> Move account to inactive OU or inactive state
   -> Preserve evidence for retention period
   -> Delete only after retention policy allows
```

This separates employment-record retention from active access control. HR may retain terminated employee records for legal, payroll, tax, investigation, or audit reasons, while IAM removes downstream access from systems where the user should no longer authenticate.

## Non-Human Identity / Orphan Account Discovery Pattern

```text
Service account created directly in LDAP
        |
        v
LDAP reconciliation runs
        |
        v
midPoint discovers account with no matching governed focus object
        |
        v
Account is classified as unmatched
        |
        v
Governance disposition required:
        - assign owner
        - validate business justification
        - remove unauthorized access
        - document exception if temporarily required
        - include in access review
```

## Design Principle

The architecture demonstrates a core IAM control pattern:

```text
Authoritative identity source determines eligibility.
IGA platform governs lifecycle and access decisions.
Target systems enforce account state and access.
Audit evidence proves the control operated.
```










