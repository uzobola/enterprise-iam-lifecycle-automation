# Screenshot Evidence Map

This evidence map explains what each screenshot proves in the IAM lifecycle implementation.

| Evidence ID | Evidence File | What It Shows | What It Proves | Control / Risk Supported |
|---|---|---|---|---|
| EVID-01 | `screenshots/01-simplifyhr-before-state.png` | Initial workforce records in SimplifyHR | HR source contained the authoritative identity population before IAM processing | Authoritative source validation |
| EVID-02 | `screenshots/02-midpoint-hr-resource-inbound-mappings.png` | HR-to-midPoint inbound mappings | HR attributes were normalized into governed identity attributes | Controlled identity data ingestion |
| EVID-03 | `screenshots/03-midpoint-users-after-hr-reconciliation.png` | Users created in midPoint after reconciliation | HR records became governed focus objects | Automated identity creation |
| EVID-04 | `screenshots/04-openldap-resource-outbound-mappings.png` | midPoint-to-LDAP outbound mappings | Governed identity attributes were mapped to downstream LDAP account attributes | Controlled target provisioning |
| EVID-05 | `screenshots/05-ldap-accounts-provisioned.png` | LDAP accounts visible in phpLDAPadmin | Accounts were provisioned to the downstream directory through IAM workflow | No direct manual target account creation |
| EVID-06 | `screenshots/06-joiner-before-after.png` | New joiner created in HR and provisioned downstream | Joiner workflow created identity and LDAP account through reconciliation | Automated onboarding |
| EVID-07 | `screenshots/07-leaver-simplifyhr-terminated.png` | Oliver Bennett marked Terminated in SimplifyHR | HR retained the record while removing the user from active identity population | Authoritative lifecycle event |
| EVID-08 | `screenshots/08-leaver-midpoint-disabled.png` | Oliver disabled in midPoint | midPoint consumed the HR lifecycle state and disabled the governed identity | Centralized lifecycle governance |
| EVID-09 | `screenshots/09-leaver-ldap-account-removed.png` | Oliver removed from active LDAP target location | Downstream LDAP access was removed after HR-driven reconciliation | Timely access removal |
| EVID-10 | `screenshots/10-audit-log-lifecycle-events.png` | midPoint audit log / records | Lifecycle actions were system-recorded with timestamp and initiator context | Auditability and traceability |
| EVID-11 | `screenshots/11-unmatched-service-account.png` | Service account detected as unmatched | An LDAP account existed without a matching governed identity or HR source | Orphan / NHI governance finding |