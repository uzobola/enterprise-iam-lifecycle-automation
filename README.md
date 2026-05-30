# Enterprise IAM Lifecycle Automation with midPoint and OpenLDAP

**HR-driven workforce identity lifecycle automation using midPoint and OpenLDAP.**

This project implements production-aligned Identity Governance and Administration patterns using midPoint and OpenLDAP — demonstrating how an HR-driven lifecycle pipeline provisions and governs workforce identities across source, IGA, and directory layers.

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

| Tool | Purpose |
|---|---|
| midPoint | Identity governance, reconciliation, lifecycle automation, and access lifecycle orchestration |
| SimplifyHR / CSV Source | Authoritative workforce identity source for joiner and leaver events |
| OpenLDAP / 389 Directory Server | Downstream enterprise directory target for provisioned accounts |
| phpLDAPadmin | Directory verification tool used to validate LDAP account state |
| Groovy | Attribute transformation and lifecycle logic for mappings |
| Linux | Platform layer supporting directory services and IAM components |
| GitHub | Documentation, evidence packaging, and portfolio repository hosting |

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

Oliver Bennett was marked as **Terminated** in SimplifyHR. The HR source retained Oliver as a terminated workforce record, but he was removed from the active identity population. After reconciliation, midPoint detected the HR status change, disabled the midPoint user, and triggered deletion/removal of the corresponding OpenLDAP account from `ou=people` in the project configuration.

Result: the terminated employee remained visible in the HR source as a terminated record, while the downstream LDAP account was removed from the active directory target.

> **Production note:** In many enterprise environments, the preferred production pattern is to disable the account first, move it to an inactive organizational unit or apply an account lock, preserve audit history for a defined retention period, and delete only after the retention policy allows it. The project simplified this by removing the account from OpenLDAP after termination.

### Phase 5 — Non-Human Identity / Orphan Account Discovery

A service account was created directly in LDAP to simulate an account provisioned outside the IAM governance process. During LDAP reconciliation, midPoint detected the account as an unmatched shadow because there was no corresponding governed focus object or HR identity record.

Result: the unmanaged service account was identified as a governance finding requiring disposition: link it to an approved owner, remove it if unauthorized, or document it as an exception with review and expiration requirements.

---

## Attribute Mapping Design

### HR Source to midPoint

| HR Attribute | midPoint Attribute | Transformation | Purpose | Design Note |
|---|---|---|---|---|
| `empid` | `name` | As-is | Project username / primary identifier | Used for exact-match correlation in this implementation |
| `empid` | `employeeNumber` | As-is | Stable employee identifier | Better correlation key than name or email |
| `empid` | `emailAddress` | Groovy: `input + '@simplifytech.com'` | Project-generated email address | Production email should follow enterprise naming policy |
| `firstname` | `givenName` | As-is | First name | Standard identity profile attribute |
| `lastname` | `familyName` | As-is | Last name | Maps later to LDAP surname attribute |
| `department` | `organizationalUnit` | As-is | Department placement | Supports RBAC and mover logic |
| `costcenter` | `costCenter` | As-is | Business cost center | Supports reporting and downstream attribute mapping |
| `status` | `activation/administrativeStatus` | Groovy lifecycle logic | Active or disabled identity state | Drives joiner/leaver behavior |

### midPoint to OpenLDAP

| midPoint Attribute | LDAP Attribute | Transformation | Purpose | Design Note |
|---|---|---|---|---|
| `givenName` | `givenName` | As-is | First name | Standard LDAP person attribute |
| `familyName` | `sn` | As-is | Surname / last name | Required by many LDAP person object classes |
| `givenName` + `familyName` | `cn` | Groovy: `givenName + ' ' + familyName` | Common name | Generates readable full name |
| `name` | `dn` | Groovy DN logic | LDAP distinguished name | Routes account into directory tree |
| `emailAddress` | `mail` | As-is | Email address | Directory profile attribute |
| `costCenter` | `departmentNumber` | As-is | Cost center tracking | Supports reporting and downstream classification |
| `employeeNumber` | `employeeNumber` | As-is | Employee identifier | Preserves identity traceability in LDAP |

---

## Enterprise Platform Equivalents

This project used midPoint and OpenLDAP in this environment, but the same IAM architecture patterns apply to common enterprise IAM and IGA platforms.

| Project Component              | Enterprise Equivalent                                                      | Conceptual Meaning                                   |
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

Correlation determines whether an incoming HR record or LDAP account belongs to an existing midPoint user. In this project implementation, the correlation rule uses exact matching on the `name` attribute, which holds the HR employee ID value.

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

### Project Behavior

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
OpenLDAP account deleted / removed from ou=people in project configuration
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
| IAM evidence validator output | HR and LDAP state were independently compared to identify lifecycle, provisioning, NHI, and manager-assignment findings |

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

## IAM Evidence Validator

This project includes a Python-based IAM evidence validator that compares the authoritative HR source against the LDAP directory state and produces a structured findings report mapped to SOC 2-style access controls.

The validator checks for:

- Terminated employees with active LDAP accounts
- Active employees missing LDAP accounts
- LDAP accounts with no matching HR record
- Attribute drift between HR and LDAP
- Missing manager assignments
- Self-manager review risks
- Service accounts requiring non-human identity governance review

The output is a JSON evidence report with severity ratings, remediation guidance, source/target snapshots, and SOC 2 control mappings.

Running the validator against this environment produced 4 findings:

- 1 MEDIUM finding: Oliver Bennett’s inactive LDAP account was not locked in `ou=inactive`
- 3 LOW findings: manager assignment review gaps

This demonstrates how IAM lifecycle evidence can be converted into structured GRC findings for access control validation and remediation tracking.

```bash
pip install -r requirements.txt
LDAP_PASSWORD='your-password' python automation/iam_evidence_validator.py
```


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

The project implementation uses employee ID as the `name` value for exact matching. This works for this environment because it is stable and unique. In production, I would usually separate the correlation key from the username and email address.

```text
Correlation identifier ≠ Login username ≠ Email address
```

### 4. Provisioning Requires a Role Construction

Connecting a target resource is not enough. midPoint needs an assignment or role construction that tells it when to create accounts on the target resource.

### 5. Disablement Is Usually Preferred Before Deletion

The project implementation demonstrated removal from OpenLDAP after termination. In production, I would typically disable the account or move it to an inactive OU first, then delete later based on retention policy.

### 6. Unmatched Accounts Are Governance Findings

An account discovered in a target system without a matching governed identity is not just a technical mismatch. It is a governance finding. The account must be reviewed for ownership, business justification, access scope, approval history, and remediation timeline.

### 7. Audit Evidence Is Part of the Control

A lifecycle process is not complete just because the account changed. The implementation must also prove what happened, when it happened, and which identity event triggered the change.

---

## Business Value

This implementation reduces manual identity administration, improves onboarding and offboarding consistency, creates audit-ready lifecycle evidence, and demonstrates how an IGA platform can enforce access lifecycle controls across downstream systems.

It also shows how identity governance can support compliance readiness by producing evidence for authorized provisioning, timely access termination, access traceability, and unmanaged account detection.

---