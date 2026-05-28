# File: `mappings/hr-to-midpoint-mapping.md`

```markdown
# HR Source to midPoint Mapping

This document describes the inbound identity mappings from the SimplifyHR source into midPoint. These mappings normalize HR data into governed identity attributes.

## Mapping Table

| HR Source Attribute | midPoint Attribute | Transformation | Purpose | Production Design Note |
|---|---|---|---|---|
| `empid` | `name` | As-is | Project username / primary identifier | In production, username may follow a naming standard such as firstname.lastname |
| `empid` | `employeeNumber` | As-is | Stable employee identifier | Strong correlation key because it is less likely to change than name or email |
| `empid` | `emailAddress` | Groovy: `input + '@simplifytech.com'` | Project-generated email address | In production, email should usually be generated from enterprise email policy, not employee ID |
| `firstname` | `givenName` | As-is | First name | Standard identity profile attribute |
| `lastname` | `familyName` | As-is | Last name | Later maps to LDAP `sn` |
| `department` | `organizationalUnit` | As-is | Department placement | Used later for RBAC / mover logic |
| `costcenter` | `costCenter` | As-is | Business cost center | Supports reporting, access decisions, and target attribute mapping |
| `status` | `activation/administrativeStatus` | Groovy status logic | Lifecycle state | Drives enabled/disabled behavior |

## Lifecycle Status Logic

The project uses a Groovy expression to convert HR status into midPoint activation state.

```groovy
import com.evolveum.midpoint.xml.ns._public.common.common_3.ActivationStatusType

if (input == 'Active') {
    return ActivationStatusType.ENABLED
} else {
    return ActivationStatusType.DISABLED
}
````

## Correlation Design

The implementation uses exact matching on the `name` attribute, which contains the HR employee ID value in this project.

```text
HR empid -> midPoint name -> exact correlation match
```

## Why Employee ID Matters

Employee ID is a stronger correlation attribute than first name, last name, or email because:

* Names can change.
* Emails can change.
* Two employees can have the same name.
* Employee ID is designed to be unique and stable.
* Stable identifiers reduce duplicate identity risk.

## Production Design Note

In production, I would separate these concepts:

```text
Correlation identifier = stable employee number
Login username = enterprise naming standard
Email address = corporate email policy
```

The project uses employee ID as a practical stable identifier for the implementation, while documenting how the design would be adapted in a production IAM environment.