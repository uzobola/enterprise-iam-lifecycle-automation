# GRC Control Mapping

This document maps the IAM lifecycle implementation to governance, risk, and compliance evidence themes. The mappings are illustrative and should be validated against an organization's official control library, audit scope, and auditor expectations.

## Control Mapping Table

| Control Area | IAM Event / Evidence | Control Objective | Example Framework Alignment | Evidence Artifact |
|---|---|---|---|---|
| Authorized Provisioning | HR reconciliation creates midPoint focus object | New identities are created through an authorized source and governed workflow | SOC 2 CC6.1 / CC6.2 | `03-midpoint-users-after-hr-reconciliation.png` |
| Access Provisioning | Employee role construction provisions LDAP account | Downstream access is granted through approved IAM logic, not direct manual creation | SOC 2 CC6.1 / CC6.2 | `05-ldap-accounts-provisioned.png` |
| Identity Data Integrity | Inbound mappings normalize HR attributes | Identity attributes come from an authoritative source and are consistently mapped | SOC 2 CC6.1 / CC6.2 | `02-midpoint-hr-resource-inbound-mappings.png` |
| Target Account Governance | Outbound mappings provision LDAP attributes | Target accounts receive controlled attributes from the IGA system | SOC 2 CC6.1 / CC6.2 | `04-openldap-resource-outbound-mappings.png` |
| Timely Access Termination | HR termination triggers midPoint disablement and LDAP removal | Access is removed when the user is no longer eligible | SOC 2 CC6.3 | `07-leaver-simplifyhr-terminated.png`, `08-leaver-midpoint-disabled.png`, `09-leaver-ldap-account-removed.png` |
| Auditability | Audit logs record lifecycle actions | Access changes are traceable to system events with timestamps | SOC 2 CC6.1 / CC7.2 | `10-audit-log-lifecycle-events.png` |
| Orphan / NHI Governance | Unmatched service account detected | Accounts outside the identity governance process are identified and reviewed | SOC 2 CC6.1 / CC6.2 / CC6.3 | `11-unmatched-service-account.png` |
| Exception Management | Unmatched account requires disposition | Exceptions are owned, justified, reviewed, and remediated | SOC 2 CC6.2 / CC6.3 | `11-unmatched-service-account.png` + disposition notes |

## Control Narrative

This project demonstrates how IAM implementation work can produce audit-ready evidence. The goal is not only to provision and remove accounts, but to prove that the lifecycle control operated as intended.

The control pattern is:

```text
Source event -> IGA reconciliation -> Target account action -> Audit evidence -> Control validation
````

## Example Control Statements

### IAM-001 — Authoritative Source Provisioning

**Control Objective:** Workforce identities should be created from an authorized source of truth.

**Implementation Evidence:** SimplifyHR records were ingested through configured inbound mappings and reconciled into midPoint user focus objects.

**Evidence:** `02-midpoint-hr-resource-inbound-mappings.png`, `03-midpoint-users-after-hr-reconciliation.png`

### IAM-002 — Governed Target Account Provisioning

**Control Objective:** Downstream accounts should be provisioned through the IGA platform using controlled mappings and role-based logic.

**Implementation Evidence:** OpenLDAP outbound mappings and Employee role construction provisioned directory accounts from midPoint.

**Evidence:** `04-openldap-resource-outbound-mappings.png`, `05-ldap-accounts-provisioned.png`

### IAM-003 — Timely Leaver Access Removal

**Control Objective:** Access should be removed when a user is terminated or no longer eligible.

**Implementation Evidence:** Oliver Bennett was marked Terminated in SimplifyHR, disabled in midPoint, and removed from active LDAP access after reconciliation.

**Evidence:** `07-leaver-simplifyhr-terminated.png`, `08-leaver-midpoint-disabled.png`, `09-leaver-ldap-account-removed.png`

### IAM-004 — Unmanaged Account Detection

**Control Objective:** Accounts created outside the governed IAM process should be detected and dispositioned.

**Implementation Evidence:** LDAP reconciliation identified an unmatched service account without a matching governed identity.

**Evidence:** `11-unmatched-service-account.png`

## Audit-Ready Evidence Characteristics

Good IAM evidence should show:

* Who or what changed
* When the change happened
* Which system initiated the change
* Which source record triggered the change
* What downstream account or entitlement changed
* Whether the action matched policy
* What remediation is required for exceptions

## Why This Matters

A lifecycle process is incomplete if it cannot be proven. This project connects IAM engineering with GRC evidence by showing how access lifecycle events can support compliance testing, audit readiness, and risk-based remediation.
