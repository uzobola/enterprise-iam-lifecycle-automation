# Enterprise IAM Lifecycle Automation with midPoint and OpenLDAP

**HR-driven workforce identity lifecycle automation using midPoint and OpenLDAP.**

This project simulates an enterprise Identity Governance and Administration implementation where an HR source acts as the authoritative identity system, midPoint performs identity governance and reconciliation, and OpenLDAP represents a downstream enterprise directory.

The implementation demonstrates joiner automation, HR-to-IGA inbound mapping, target-system outbound mapping, identity correlation, reconciliation, LDAP account provisioning, leaver handling, non-human identity discovery, and audit evidence validation.

---

## Business Problem

Many organizations still rely on manual identity administration for onboarding, offboarding, and access updates. This creates security and compliance risk because accounts may be created inconsistently, terminated users may retain access, unmanaged service accounts may exist outside governance, and auditors may lack reliable evidence showing when access changed and which system triggered the change.

The business impact is significant. IBM’s 2025 Cost of a Data Breach Report placed the global average cost of a data breach at **USD 4.44 million**. Identity lifecycle failures are one of the control gaps that can contribute to access misuse, delayed termination, weak accountability, and audit findings.

This project addresses those risks by implementing an HR-driven IAM lifecycle workflow where identity records are imported from an authoritative source, correlated to governed user objects, provisioned into a directory, updated through reconciliation, and validated through audit evidence.

---

## Solution Architecture

```text
SimplifyHR / CSV Source
Authoritative workforce identity feed
        |
        | Inbound mappings
        v
midPoint IGA Platform
Correlation, reconciliation, lifecycle logic
        |
        | Role construction and outbound mappings
        v
OpenLDAP / 389 Directory Server
Provisioned directory accounts
        |
        | Reconciliation and account discovery
        v
Audit Evidence + NHI / Orphan Account Findings
Object adds, object modifications, reconciliation results, unmatched accounts
```

---

## Tools and Technologies

| Tool                            | Purpose                                                   |
| ------------------------------- | --------------------------------------------------------- |
| midPoint                        | Identity governance, reconciliation, lifecycle automation |
| SimplifyHR / CSV                | Authoritative HR identity source                          |
| OpenLDAP / 389 Directory Server | Target enterprise directory                               |
| phpLDAPadmin                    | LDAP account verification                                 |
| Groovy                          | Attribute transformation and lifecycle logic              |
| Linux                           | Directory service and project implementation platform support                |

---

## IAM Concepts Demonstrated

* Authoritative source integration
* Joiner lifecycle automation
* Leaver lifecycle handling
* HR-to-IGA inbound mapping
* IGA-to-directory outbound mapping
* Correlation rules
* Reconciliation tasks
* Focus objects and account shadows
* Role construction / inducement-based provisioning
* LDAP account provisioning
* Non-human identity discovery
* Unmatched account detection
* Audit evidence validation
* Production design considerations for disablement vs deletion

---

## Implementation Overview

### Phase 1 — HR Source to midPoint

SimplifyHR was configured as a CSV source resource in midPoint. The source schema was discovered, inbound mappings were configured, synchronization reactions were defined, and reconciliation was executed.

Result: employee records from the HR source were created as governed user focus objects in midPoint.

### Phase 2 — midPoint to OpenLDAP

OpenLDAP was configured as a target resource. The LDAP object type was defined, outbound mappings were configured, and the Employee role was updated with an OpenLDAP account construction.

Result: governed midPoint users were provisioned into OpenLDAP as directory accounts.

### Phase 3 — Joiner Process

A new employee was added in SimplifyHR. After reconciliation, midPoint detected the new HR record, created the user focus object, assigned the Employee role, and provisioned the LDAP account.

Result: a new workforce identity was created and provisioned end-to-end with no manual account creation in LDAP.

### Phase 4 — Leaver Process

Oliver Bennett was marked as **Terminated** in SimplifyHR. The HR source retained Oliver as a terminated workforce record, but he was removed from the active identity population. After reconciliation, midPoint detected the HR status change, disabled the midPoint user, and triggered deletion/removal of the corresponding OpenLDAP account from `ou=people` in the lab configuration.

Result: the terminated employee remained visible in the HR source as a terminated record, while the downstream LDAP account was removed from the active directory target.

> **Production note:** In many enterprise environments, the preferred production pattern is to disable the account first, move it to an inactive organizational unit or apply an account lock, preserve audit history for a defined retention period, and delete only after the retention policy allows it. The lab simplified this by removing the account from OpenLDAP after termination.

### Phase 5 — Non-Human Identity / Orphan Account Discovery

A service account was created directly in LDAP to simulate an account provisioned outside the IAM governance process. During LDAP reconciliation, midPoint detected the account as an unmatched shadow because there was no corresponding governed focus object or HR identity record.

Result: the unmanaged service account was identified as a governance finding requiring disposition: link it to an approved owner, remove it if unauthorized, or document it as an exception with review and expiration requirements.

---

## Attribute Mapping Design

### HR Source to midPoint

| HR Attribute | midPoint Attribute                | Purpose                                    | Design Note                                                     |
| ------------ | --------------------------------- | ------------------------------------------ | --------------------------------------------------------------- |
| `empid`      | `name`                            | Lab username / primary resource identifier | Used by the lab for exact matching                              |
| `empid`      | `emailAddress`                    | Lab-generated email address                | Production design would usually separate email from employee ID |
| `firstname`  | `givenName`                       | First name                                 | Direct profile mapping                                          |
| `lastname`   | `familyName`                      | Last name                                  | Later maps to LDAP surname                                      |
| `department` | `organizationalUnit`              | Department placement                       | Supports later RBAC/mover logic                                 |
| `costcenter` | `costCenter`                      | Business cost center                       | Supports reporting and downstream attributes                    |
| `status`     | `activation/administrativeStatus` | Lifecycle state                            | Drives joiner/leaver behavior                                   |

### midPoint to OpenLDAP

| midPoint Attribute       | LDAP Attribute     | Purpose                 | Design Note                        |
| ------------------------ | ------------------ | ----------------------- | ---------------------------------- |
| `givenName`              | `givenName`        | First name              | Direct mapping                     |
| `familyName`             | `sn`               | Surname / last name     | Required LDAP naming convention    |
| `givenName + familyName` | `cn`               | Common name             | Generated with Groovy expression   |
| `name`                   | `dn`               | LDAP distinguished name | Routes active users to `ou=people` |
| `emailAddress`           | `mail`             | Email address           | Generated from lab identifier      |
| `costCenter`             | `departmentNumber` | Cost center tracking    | Business reporting attribute       |
| `employeeNumber`         | `employeeNumber`   | Employee identifier     | Supports identity traceability     |

---

## Enterprise Platform Equivalents

This project used midPoint and OpenLDAP in a lab environment, but the same IAM architecture patterns apply to common enterprise IAM and IGA platforms.

| Lab / Project Component              | Enterprise Equivalent                                                      | Conceptual Meaning                                   |
| ------------------------------------ | -------------------------------------------------------------------------- | ---------------------------------------------------- |
| midPoint                             | SailPoint IdentityNow / IdentityIQ, Saviynt, Microsoft Entra ID Governance | IGA platform / identity governance control plane     |
| SimplifyHR CSV connector             | Workday, SuccessFactors, UKG, REST API, SCIM, HR flat-file feed            | Authoritative source integration                     |
| HR inbound mappings                  | Source attribute mappings                                                  | Normalizes HR attributes into identity attributes    |
| Correlation rule                     | Authoritative source correlation configuration                             | Matches source records to existing identities        |
| Reconciliation task                  | Aggregation task / identity refresh / account aggregation                  | Compares identity state across systems               |
| Focus object                         | Identity cube / user identity profile                                      | Central governed identity record                     |
| Shadow object                        | Account link / account object / projection                                 | Representation of an account on a target system      |
| Role construction / inducement       | Access profile, provisioning policy, account creation policy               | Defines when and how target accounts are provisioned |
| OpenLDAP target resource             | Active Directory, LDAP directory, SaaS app, cloud account, database        | Downstream system receiving provisioned access       |
| `nsAccountLock` / LDAP lock behavior | AD `userAccountControl`, Entra accountEnabled, SaaS active flag            | Target-specific account disablement control          |
| phpLDAPadmin verification            | ADUC, Entra admin center, SaaS admin console, API query                    | Independent target-system validation                 |
| Audit Log Viewer                     | Audit reports, access change history, SIEM evidence                        | Evidence of lifecycle events and control execution   |

---

## Correlation and Reconciliation Design

Correlation determines whether an incoming HR record or LDAP account belongs to an existing midPoint user. In this lab, the correlation rule uses exact matching on the `name` attribute, which holds the HR employee ID value.

Reconciliation compares source and target data against midPoint’s governed identity state. It detects new records, updates changed identities, links existing accounts, identifies unmatched accounts, and triggers provisioning or lifecycle actions.

```text
Mapping = translate attributes
Correlation = match records to identities
Reconciliation = compare systems and apply lifecycle logic
Provisioning = create, update, disable, or remove target accounts
```

---

## Joiner Flow

```text
New employee created in SimplifyHR
        |
        v
SimplifyHR reconciliation runs
        |
        v
midPoint detects unmatched HR record
        |
        v
User focus object created
        |
        v
Employee role assigned
        |
        v
OpenLDAP account provisioned
        |
        v
Audit trail records lifecycle event
```

---

## Leaver Flow

### Production Pattern

```text
Employee marked terminated in HR
        |
        v
Reconciliation detects lifecycle change
        |
        v
midPoint user disabled
        |
        v
Target account disabled / locked
        |
        v
Account moved to inactive OU or retained under inactive state
        |
        v
Audit evidence captured
        |
        v
Deletion only after retention policy allows it
```

### Lab Behavior

```text
Oliver Bennett marked Terminated in SimplifyHR
HR record retained, active identity population reduced
        |
        v
SimplifyHR reconciliation runs
        |
        v
midPoint detects HR status change
        |
        v
midPoint user becomes disabled
        |
        v
OpenLDAP account deleted / removed from ou=people in lab configuration
        |
        v
Audit trail records lifecycle event
```

---

## Non-Human Identity / Orphan Account Discovery Flow

```text
Service account created directly in LDAP
        |
        v
LDAP reconciliation runs
        |
        v
midPoint discovers account with no matching focus object
        |
        v
Account classified as unmatched
        |
        v
Governance disposition required
        |
        v
Link to owner, remove if unauthorized, or document exception
```

---

## Evidence Captured

| Evidence                                        | What It Proves                                                                   |
| ----------------------------------------------- | -------------------------------------------------------------------------------- |
| SimplifyHR records                              | HR source acts as identity authority                                             |
| midPoint users page                             | HR records were converted into governed focus objects                            |
| Inbound mapping configuration                   | HR attributes were mapped into midPoint identity attributes                      |
| OpenLDAP account list                           | Directory accounts were provisioned from midPoint                                |
| phpLDAPadmin verification                       | LDAP target state matched expected provisioning result                           |
| Joiner before/after screenshots                 | New employee was created and provisioned through reconciliation                  |
| Leaver before/after screenshots                 | HR source retained Oliver as terminated while downstream LDAP access was removed |
| Audit logs / records                            | Lifecycle events were logged with timestamps and initiator details               |
| Unmatched service account screenshot            | LDAP account existed without an approved identity owner or HR source             |
| Reconciliation result showing unmatched account | Governance process can detect accounts created outside IAM                       |

---

## GRC and Compliance Evidence Mapping

This project connects IAM implementation work to audit evidence. The table below shows how the lifecycle events can support control testing and compliance reporting.

| Audit / Evidence Event                                          | Control Evidenced                          | Example Framework Mapping | Why It Matters                                                                    |
| --------------------------------------------------------------- | ------------------------------------------ | ------------------------- | --------------------------------------------------------------------------------- |
| HR reconciliation creates user focus object                     | Authorized provisioning                    | SOC 2 CC6.2               | Users are registered and granted access through an authorized process             |
| Employee role construction provisions LDAP account              | Controlled access implementation           | SOC 2 CC6.1 / CC6.2       | Access is issued through governed IAM workflow, not manual target-system creation |
| Leaver reconciliation disables/removes active access            | Timely access termination                  | SOC 2 CC6.3               | Access is removed when no longer required                                         |
| Audit log shows system-initiated lifecycle event                | Traceability and accountability            | SOC 2 CC6.1 / CC7.2       | The organization can prove what happened, when, and through which process         |
| Unmatched service account discovered during LDAP reconciliation | Unauthorized / unmanaged account detection | SOC 2 CC6.1 / CC6.2       | Accounts outside the governance process are identified for review                 |
| Disposition decision for unmanaged account                      | Exception management and access review     | SOC 2 CC6.2 / CC6.3       | Exceptions are documented, owned, reviewed, and remediated                        |

> Note: Framework mappings are illustrative and should be validated against the organization’s control library, audit scope, and auditor expectations.

---

## Security Risks Addressed

* Manual account creation errors
* Lack of authoritative identity source
* Duplicate identities caused by weak correlation
* Delayed onboarding for new employees
* Terminated users retaining active directory access
* Weak evidence for joiner and leaver events
* Inconsistent deprovisioning behavior across systems
* Poor visibility into who created, changed, or removed access
* Non-human identities created outside governance
* Service accounts without a named owner, approval record, or review date

---

## Design Decisions and Lessons Learned

### 1. HR Must Remain the Source of Truth

The HR source should be read by the IAM platform, not overwritten by it. Disabling delete capability on the HR source reduces the risk of accidentally deleting authoritative employee records from the source system.

In this implementation, the leaver event originates from SimplifyHR. Oliver Bennett is retained as a terminated HR record, while reconciliation drives the downstream access-removal action in OpenLDAP.

### 2. HR Retention Is Different from Active Access

A terminated employee should not disappear from the HR system immediately. HR systems often retain former employee records for legal, payroll, tax, audit, and investigation purposes. IAM should consume the lifecycle status from HR and remove or disable access in downstream systems without deleting the authoritative employment history.

The key design distinction is:

```text
HR record retention = preserve employment history and audit context
Active identity population = users currently eligible for access
Downstream access = accounts and entitlements controlled by IAM
```

Oliver Bennett remained in SimplifyHR as a terminated record, but his active access was removed from the downstream LDAP target.

### 3. Correlation Keys Should Be Stable

The lab uses employee ID as the `name` value for exact matching. This works for training because it is stable and unique. In production, I would usually separate the correlation key from the username and email address.

```text
Correlation identifier ≠ Login username ≠ Email address
```

### 4. Provisioning Requires a Role Construction

Connecting a target resource is not enough. midPoint needs an assignment or role construction that tells it when to create accounts on the target resource.

### 5. Disablement Is Usually Preferred Before Deletion

The lab demonstrated removal from OpenLDAP after termination. In production, I would typically disable the account or move it to an inactive OU first, then delete later based on retention policy.

### 6. Unmatched Accounts Are Governance Findings

An account discovered in a target system without a matching governed identity is not just a technical mismatch. It is a governance finding. The account must be reviewed for ownership, business justification, access scope, approval history, and remediation timeline.

### 7. Audit Evidence Is Part of the Control

A lifecycle process is not complete just because the account changed. The implementation must also prove what happened, when it happened, and which identity event triggered the change.

---

## Business Value

This implementation reduces manual identity administration, improves onboarding and offboarding consistency, creates audit-ready lifecycle evidence, and demonstrates how an IGA platform can enforce access lifecycle controls across downstream systems.

It also shows how identity governance can support compliance readiness by producing evidence for authorized provisioning, timely access termination, access traceability, and unmanaged account detection.

---

## Repository Structure

```text
enterprise-iam-lifecycle-automation/
├── README.md
├── architecture/
│   └── iam-lifecycle-architecture.png
├── screenshots/
│   ├── 01-simplifyhr-before-state.png
│   ├── 02-midpoint-hr-resource-inbound-mappings.png
│   ├── 03-midpoint-users-after-hr-reconciliation.png
│   ├── 04-openldap-resource-outbound-mappings.png
│   ├── 05-ldap-accounts-provisioned.png
│   ├── 06-joiner-before-after.png
│   ├── 07-leaver-simplifyhr-terminated.png
│   ├── 08-leaver-midpoint-disabled.png
│   ├── 09-leaver-ldap-account-removed.png
│   ├── 10-audit-log-lifecycle-events.png
│   └── 11-unmatched-service-account.png
├── evidence/
│   ├── evidence-map.md
│   └── grc-control-mapping.md
├── mappings/
│   ├── hr-to-midpoint-mapping.md
│   └── midpoint-to-openldap-mapping.md
└── lessons-learned.md
```

---

## Screenshot Evidence Map

| Screenshot                                    | File Name                                       | What It Proves                                                                      | README Section Supported            |
| --------------------------------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------- |
| SimplifyHR initial workforce / active records | `01-simplifyhr-before-state.png`                | HR source contained the workforce population before IAM processing                  | Business Problem / Phase 1          |
| SimplifyHR inbound mappings                   | `02-midpoint-hr-resource-inbound-mappings.png`  | HR attributes were mapped into midPoint identity attributes                         | Attribute Mapping Design            |
| midPoint Users page after HR reconciliation   | `03-midpoint-users-after-hr-reconciliation.png` | HR records became governed midPoint focus objects                                   | Phase 1 / Evidence Captured         |
| OpenLDAP outbound mappings                    | `04-openldap-resource-outbound-mappings.png`    | midPoint attributes were mapped to LDAP account attributes                          | Phase 2 / Attribute Mapping Design  |
| LDAP accounts provisioned in phpLDAPadmin     | `05-ldap-accounts-provisioned.png`              | Accounts were created in the downstream directory through IAM provisioning          | Phase 2 / Evidence Captured         |
| Joiner before/after screenshots               | `06-joiner-before-after.png`                    | A new employee was created in HR and provisioned through reconciliation             | Joiner Flow                         |
| SimplifyHR leaver state for Oliver Bennett    | `07-leaver-simplifyhr-terminated.png`           | HR retained Oliver as terminated while removing him from active identity population | Leaver Flow                         |
| midPoint disabled state for Oliver Bennett    | `08-leaver-midpoint-disabled.png`               | midPoint detected the HR lifecycle change and disabled the governed identity        | Leaver Flow / GRC Mapping           |
| LDAP account removed from active target       | `09-leaver-ldap-account-removed.png`            | Downstream active LDAP access was removed after reconciliation                      | Leaver Flow / Evidence Captured     |
| Audit log / Records lifecycle events          | `10-audit-log-lifecycle-events.png`             | Lifecycle events were system-recorded with timestamps and initiator details         | GRC and Compliance Evidence Mapping |
| Unmatched service account / NHI finding       | `11-unmatched-service-account.png`              | LDAP contained an account without a governed identity owner or HR source            | NHI / Orphan Account Discovery      |

---

## Portfolio Card Copy

**Title:** Enterprise IAM Lifecycle Automation
**Category:** Identity Governance
**Tech Stack:** midPoint · OpenLDAP · LDAP · Groovy · Linux · IGA · Reconciliation

**Description:**
Implemented an HR-driven IAM lifecycle pipeline using midPoint and OpenLDAP. The project demonstrates authoritative source integration, attribute mapping, identity correlation, reconciliation, role-based LDAP provisioning, Joiner/Leaver lifecycle automation, non-human identity discovery, and audit evidence validation.

**Business Risk Addressed:**
Manual identity administration, delayed offboarding, unmanaged service accounts, weak audit evidence, and inconsistent lifecycle enforcement across downstream systems.

**Evidence Produced:**
Architecture diagram, inbound/outbound mapping tables, joiner/leaver screenshots, LDAP verification, audit logs, unmatched account finding, and GRC control mapping.

---

## Interview Talking Points

* Explain why HR should be the authoritative source for workforce identities.
* Explain the difference between inbound and outbound mappings.
* Explain how correlation prevents duplicate identities.
* Explain the difference between reconciliation and provisioning.
* Explain why target systems require their own attribute mappings.
* Explain why connecting a resource is not enough without a role construction.
* Explain why production environments often disable accounts before deleting them.
* Explain how reconciliation can detect unmanaged service accounts and non-human identities.
* Explain how audit evidence supports compliance and access governance.
* Explain how this pattern maps to SailPoint, Saviynt, Okta, Entra ID, Active Directory, and AWS IAM Identity Center.

---

## Resume Bullet

Designed and implemented an enterprise IAM lifecycle automation project using midPoint IGA and OpenLDAP, integrating an HR source for automated identity creation, attribute mapping, identity correlation, reconciliation, LDAP provisioning, leaver handling, non-human identity discovery, and audit evidence validation mapped to access governance controls.

Implemented HR-driven IAM lifecycle pipeline in midPoint IGA — configured CSV connector, Groovy attribute mappings, correlation rules, and role-based LDAP provisioning with automated Joiner/Leaver workflows and reconciliation-initiated audit trail demonstrating zero manual access changes.