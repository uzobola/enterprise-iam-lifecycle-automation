# NHI / Orphan Account Disposition Template

Use this template when reconciliation discovers an account that does not match a governed identity record.

## Account Details

| Field | Value |
|---|---|
| Account Name | `svc-backup` |
| Target System | OpenLDAP |
| Discovery Method | LDAP reconciliation |
| Reconciliation Status | Unmatched |
| Human Owner | TBD |
| Business Owner | TBD |
| Application / Service Purpose | TBD |
| Privilege Level | TBD |
| Last Reviewed | TBD |
| Expiration Date | TBD |

## Risk Assessment

| Risk Area | Assessment |
|---|---|
| No HR Source | Account is not tied to a workforce identity |
| No Named Owner | Accountability is unclear |
| Unknown Privileges | Access scope must be reviewed |
| Potential Persistence Risk | Service accounts can survive employee termination |
| Audit Gap | Activity may not be attributable to a person |

## Disposition Options

| Option | When to Use | Action |
|---|---|---|
| Link to governed owner | Account is legitimate and required | Assign owner, document purpose, include in access review |
| Remove account | Account is unauthorized or obsolete | Disable/delete according to policy |
| Managed exception | Account is temporarily required but not fully governed | Document approval, owner, review date, and remediation plan |

## Recommended Disposition

The account should not be ignored. It should be treated as a governance finding and assigned a formal disposition.

Recommended action:

```text
Assign named owner -> verify business justification -> review privileges -> document exception or remove account -> include in next access certification
````

```
```