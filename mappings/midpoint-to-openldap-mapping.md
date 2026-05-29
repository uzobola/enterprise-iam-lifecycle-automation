# midPoint to OpenLDAP Mapping

This document describes the outbound mappings from midPoint into OpenLDAP. These mappings define how governed identity attributes become downstream LDAP account attributes.

## Mapping Table

| midPoint Attribute | LDAP Attribute | Transformation | Purpose | Notes |
|---|---|---|---|---|
| `givenName` | `givenName` | As-is | First name | Standard LDAP person attribute |
| `familyName` | `sn` | As-is | Surname / last name | `sn` is required by many LDAP person object classes |
| `givenName` + `familyName` | `cn` | Groovy: `givenName + ' ' + familyName` | Common name | Generates readable full name |
| `name` | `dn` | Groovy DN logic | LDAP distinguished name | Routes account into directory tree |
| `emailAddress` | `mail` | As-is | Email address | Used for directory profile data |
| `costCenter` | `departmentNumber` | As-is | Cost center tracking | Supports reporting and downstream attributes |
| `employeeNumber` | `employeeNumber` | As-is | Employee identifier | Maintains identity traceability in LDAP |

## CN Generation Logic

```groovy
givenName + ' ' + familyName
````

This creates a readable LDAP common name using the user's first and last name.

## DN Routing Logic

The project includes DN logic to determine where an LDAP account should be placed.

```groovy
import com.evolveum.midpoint.xml.ns._public.common.common_3.ActivationStatusType

if (user?.activation?.administrativeStatus == ActivationStatusType.DISABLED) {
    return 'uid=' + name + ',ou=inactive,dc=simplifyiam,dc=com'
} else {
    return 'uid=' + name + ',ou=people,dc=simplifyiam,dc=com'
}
```

## Project Behavior

In this implementation, active users are provisioned into `ou=people`. During the leaver workflow, Oliver Bennett was marked Terminated in the HR source, disabled in midPoint, and removed from active LDAP access in the project configuration.

## Production Design Recommendation

For production environments, I would usually recommend:

```text
Disable account first
Move to inactive OU or locked state
Preserve account and audit evidence for retention period
Delete only after retention policy allows
```

This design helps preserve audit context, support investigation, and handle rehire scenarios.

## Target Schema Lesson

Each target system has its own schema, required attributes, account state behavior, and lifecycle controls. The role of the IAM platform is to translate governed identity attributes into the format required by each downstream target.

```text
HR speaks workforce data.
midPoint speaks governed identity.
LDAP speaks directory schema.
Mappings translate between them.
```

