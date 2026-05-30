#!/usr/bin/env python3
"""
IAM Evidence Validator
======================
Compares the HR source (CSV) against the LDAP directory state and generates
a structured findings report with severity ratings and SOC 2 control mappings.

This script implements the same governance logic that midPoint enforces through
reconciliation — but as auditable, runnable code. It answers the question:
"Does the state of the directory match what the HR source says it should be?"

Checks performed:
  - Terminated employees with active LDAP accounts (Leaver failure)
  - Active employees with no LDAP account (Joiner provisioning gap)
  - LDAP accounts with no HR record (Orphaned accounts / NHI risk)
  - Attribute drift between HR and LDAP (costcenter, name)
  - Employees with no manager assigned (Certification reviewer gap)
  - Service accounts in ou=services (NHI inventory check)

Usage:
  python iam_evidence_validator.py

  # Override connection details via environment variables:
  LDAP_HOST=192.168.1.100 LDAP_PASSWORD=secret python iam_evidence_validator.py

Output:
  - Console summary table
  - findings_<timestamp>.json  (structured evidence for GRC reporting)

Dependencies:
  pip install ldap3

Enterprise equivalent:
  This script performs the same checks as a SailPoint correlation report,
  a Saviynt access review export, or a custom reconciliation task.
  The findings map directly to SOC 2 CC6.1 / CC6.2 / CC6.3 controls.
"""

import csv
import json
import os
import sys
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timezone
from typing import Any, Optional, List, Dict

try:
    from ldap3 import Server, Connection, ALL, SUBTREE, ALL_ATTRIBUTES
    from ldap3.core.exceptions import LDAPException
except ImportError:
    print("ERROR: ldap3 not installed. Run: pip install ldap3")
    sys.exit(1)


# ── Configuration ─────────────────────────────────────────────────────────────
# Override any of these with environment variables before running.

LDAP_HOST     = os.getenv("LDAP_HOST",     "127.0.0.1")
LDAP_PORT     = int(os.getenv("LDAP_PORT", "389"))
LDAP_BIND_DN  = os.getenv("LDAP_BIND_DN",  "cn=Directory Manager")
LDAP_PASSWORD = os.getenv("LDAP_PASSWORD")

BASE_DN       = "dc=simplifyiam,dc=com"
PEOPLE_OU     = f"ou=people,{BASE_DN}"
INACTIVE_OU   = f"ou=inactive,{BASE_DN}"
SERVICES_OU   = f"ou=services,{BASE_DN}"

HR_CSV_PATH   = os.getenv("HR_CSV_PATH", "/opt/midpoint/var/hr.csv")
EMAIL_DOMAIN  = "@simplifytech.com"

# LDAP attributes to retrieve for each account
LDAP_ATTRS = [
    "uid", "givenName", "sn", "cn",
    "mail", "departmentNumber", "employeeNumber",
    "nsAccountLock", "dn"
]


# ── Finding definitions ───────────────────────────────────────────────────────
# Each finding type maps to a severity, SOC 2 control, and remediation action.

FINDING_TYPES: Dict[str, Dict[str, str]] = {
    "LEAVER_ACTIVE_ACCOUNT": {
        "severity":    "CRITICAL",
        "control":     "SOC 2 CC6.3",
        "title":       "Terminated employee retains active LDAP account",
        "remediation": "Immediately disable account — run Leaver reconciliation "
                       "or set nsAccountLock=true and move to ou=inactive",
    },
    "PROVISIONING_GAP": {
        "severity":    "HIGH",
        "control":     "SOC 2 CC6.2",
        "title":       "Active employee has no LDAP account",
        "remediation": "Run SimplifyHR reconciliation task in midPoint — "
                       "check Employee role construction is configured",
    },
    "ORPHANED_ACCOUNT": {
        "severity":    "HIGH",
        "control":     "SOC 2 CC6.1",
        "title":       "LDAP account exists with no matching HR record",
        "remediation": "Investigate ownership — link to an approved identity, "
                       "document as exception with owner and review date, "
                       "or remove if unauthorized",
    },
    "ATTRIBUTE_DRIFT_COSTCENTER": {
        "severity":    "MEDIUM",
        "control":     "SOC 2 CC6.1",
        "title":       "LDAP departmentNumber does not match HR costcenter",
        "remediation": "Run reconciliation to synchronise attribute from HR source",
    },
    "ATTRIBUTE_DRIFT_NAME": {
        "severity":    "MEDIUM",
        "control":     "SOC 2 CC6.1",
        "title":       "LDAP display name does not match HR firstname/lastname",
        "remediation": "Run reconciliation to synchronise name attributes",
    },
    "LEAVER_ACCOUNT_NOT_LOCKED": {
        "severity":    "MEDIUM",
        "control":     "SOC 2 CC6.3",
        "title":       "Terminated employee account in ou=inactive is not locked",
        "remediation": "Set nsAccountLock=true on account — "
                       "account should be locked when moved to inactive OU",
    },
    "NO_MANAGER_ASSIGNED": {
        "severity":    "LOW",
        "control":     "SOC 2 CC6.2",
        "title":       "Employee has no manager assigned in HR source",
        "remediation": "Update HR source with manager empid — "
                       "required for access certification reviewer assignment",
    },
    "SELF_MANAGER": {
        "severity":    "LOW",
        "control":     "SOC 2 CC6.2",
        "title":       "Employee is assigned as their own manager",
        "remediation": "Verify this is intentional (top-level manager) — "
                       "if not, update HR source with correct manager empid",
    },
    "NHI_SERVICE_ACCOUNT": {
        "severity":    "MEDIUM",
        "control":     "SOC 2 CC6.1",
        "title":       "Service account found in ou=services",
        "remediation": "Verify account has a named owner, documented purpose, "
                       "minimum required permissions, and a review date",
    },
}


# ── HR source reader ──────────────────────────────────────────────────────────

def load_hr_records(csv_path: str) -> Dict[str, Dict[str, str]]:
    """
    Read the HR CSV and return a dict keyed on empid.
    Raises FileNotFoundError if the CSV path does not exist.
    """
    records: Dict[str, Dict[str, str]] = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            empid = row["empid"].strip()
            records[empid] = {k.strip(): v.strip() for k, v in row.items()}
    return records


# ── LDAP reader ───────────────────────────────────────────────────────────────

def load_ldap_accounts(conn: Connection) -> Dict[str, Dict[str, Any]]:
    """
    Query LDAP for all accounts across ou=people, ou=inactive, and ou=services.
    Returns a dict keyed on uid (which holds the empid value).
    """
    accounts: Dict[str, Dict[str, Any]] = {}

    search_targets = [
        (PEOPLE_OU,   "people"),
        (INACTIVE_OU, "inactive"),
        (SERVICES_OU, "services"),
    ]

    for base, ou_label in search_targets:
        try:
            conn.search(
                search_base=base,
                search_filter="(objectClass=inetOrgPerson)",
                search_scope=SUBTREE,
                attributes=LDAP_ATTRS,
            )
            for entry in conn.entries:
                uid = str(entry.uid) if entry.uid else None
                if not uid:
                    continue
                accounts[uid] = {
                    "uid":              uid,
                    "givenName":        str(entry.givenName)        if entry.givenName        else "",
                    "sn":               str(entry.sn)               if entry.sn               else "",
                    "cn":               str(entry.cn)               if entry.cn               else "",
                    "mail":             str(entry.mail)             if entry.mail             else "",
                    "departmentNumber": str(entry.departmentNumber) if entry.departmentNumber else "",
                    "employeeNumber":   str(entry.employeeNumber)   if entry.employeeNumber   else "",
                    "nsAccountLock":    str(entry.nsAccountLock)    if entry.nsAccountLock    else "false",
                    "dn":               str(entry.entry_dn),
                    "ou":               ou_label,
                }
        except LDAPException:
            # OU may be empty — not an error condition
            pass

    return accounts


# ── Finding builder ───────────────────────────────────────────────────────────

def make_finding(
    finding_type: str,
    empid: str,
    detail: str,
    hr_data: Optional[dict] = None,
    ldap_data: Optional[dict] = None,
) -> dict:
    """Construct a single structured finding dict."""
    template = FINDING_TYPES[finding_type]
    return {
        "finding_type":  finding_type,
        "severity":      template["severity"],
        "control":       template["control"],
        "title":         template["title"],
        "empid":         empid,
        "detail":        detail,
        "remediation":   template["remediation"],
        "hr_snapshot":   hr_data  or {},
        "ldap_snapshot": ldap_data or {},
    }


# ── Validation checks ─────────────────────────────────────────────────────────

def run_checks(
    hr: Dict[str, Dict],
    ldap: Dict[str, Dict],
) -> List[Dict[str, Any]]:
    """
    Run all governance checks and return a flat list of findings.
    """
    findings: List[Dict[str, Any]] = []

    # ── HR → LDAP checks ─────────────────────────────────────────────────────
    for empid, hr_rec in hr.items():
        status     = hr_rec.get("status", "").lower()
        firstname  = hr_rec.get("firstname", "")
        lastname   = hr_rec.get("lastname", "")
        costcenter = hr_rec.get("costcenter", "")
        manager    = hr_rec.get("manager", "").strip()
        full_name  = f"{firstname} {lastname}"

        ldap_acc = ldap.get(empid)

        # 1. Terminated employee with an active account in ou=people
        if status == "terminated":
            if ldap_acc and ldap_acc["ou"] == "people":
                findings.append(make_finding(
                    "LEAVER_ACTIVE_ACCOUNT",
                    empid,
                    f"{full_name} (empid {empid}) is Terminated in HR but has "
                    f"an active account in ou=people: {ldap_acc['dn']}",
                    hr_data=hr_rec,
                    ldap_data=ldap_acc,
                ))

            # Terminated account in ou=inactive but not locked
            if ldap_acc and ldap_acc["ou"] == "inactive":
                lock = ldap_acc.get("nsAccountLock", "false").lower()
                if lock != "true":
                    findings.append(make_finding(
                        "LEAVER_ACCOUNT_NOT_LOCKED",
                        empid,
                        f"{full_name} (empid {empid}) is in ou=inactive "
                        f"but nsAccountLock is not set to true",
                        hr_data=hr_rec,
                        ldap_data=ldap_acc,
                    ))
            continue  # No further checks for terminated employees

        # 2. Active employee with no LDAP account anywhere
        if ldap_acc is None:
            findings.append(make_finding(
                "PROVISIONING_GAP",
                empid,
                f"{full_name} (empid {empid}) is Active in HR "
                f"but has no account in any LDAP OU",
                hr_data=hr_rec,
            ))
            continue  # Cannot run attribute checks without an account

        # 3. Attribute drift — costcenter vs departmentNumber
        if costcenter and ldap_acc["departmentNumber"]:
            if costcenter != ldap_acc["departmentNumber"]:
                findings.append(make_finding(
                    "ATTRIBUTE_DRIFT_COSTCENTER",
                    empid,
                    f"{full_name} (empid {empid}): "
                    f"HR costcenter='{costcenter}' but "
                    f"LDAP departmentNumber='{ldap_acc['departmentNumber']}'",
                    hr_data=hr_rec,
                    ldap_data=ldap_acc,
                ))

        # 4. Attribute drift — display name
        ldap_cn = ldap_acc.get("cn", "").strip()
        if ldap_cn and ldap_cn.lower() != full_name.lower():
            findings.append(make_finding(
                "ATTRIBUTE_DRIFT_NAME",
                empid,
                f"{full_name} (empid {empid}): "
                f"HR name='{full_name}' but LDAP cn='{ldap_cn}'",
                hr_data=hr_rec,
                ldap_data=ldap_acc,
            ))

        # 5. No manager assigned
        if not manager:
            findings.append(make_finding(
                "NO_MANAGER_ASSIGNED",
                empid,
                f"{full_name} (empid {empid}) has no manager assigned in HR — "
                f"access certification reviews cannot be automatically assigned",
                hr_data=hr_rec,
            ))

        # 6. Self-manager (flag unless intentional top-level)
        if manager and manager == empid:
            findings.append(make_finding(
                "SELF_MANAGER",
                empid,
                f"{full_name} (empid {empid}) is assigned as their own manager "
                f"(manager empid = {manager}) — verify this is a top-level manager",
                hr_data=hr_rec,
            ))

    # ── LDAP → HR checks ─────────────────────────────────────────────────────
    for uid, ldap_acc in ldap.items():

        # 7. Orphaned account — in LDAP but no HR record
        if uid not in hr and ldap_acc["ou"] in ("people", "inactive"):
            findings.append(make_finding(
                "ORPHANED_ACCOUNT",
                uid,
                f"LDAP account uid={uid} (dn: {ldap_acc['dn']}) "
                f"has no matching HR record — potential NHI or orphaned account",
                ldap_data=ldap_acc,
            ))

        # 8. Service accounts — NHI inventory
        if ldap_acc["ou"] == "services":
            findings.append(make_finding(
                "NHI_SERVICE_ACCOUNT",
                uid,
                f"Service account uid={uid} found in ou=services "
                f"(dn: {ldap_acc['dn']}) — verify governance status",
                ldap_data=ldap_acc,
            ))

    return findings


# ── Report output ─────────────────────────────────────────────────────────────

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
SEVERITY_ICONS = {
    "CRITICAL": "🔴",
    "HIGH":     "🟠",
    "MEDIUM":   "🟡",
    "LOW":      "🔵",
}


def print_summary(findings: list[dict], hr_count: int, ldap_count: int) -> None:
    """Print a formatted summary table to stdout."""
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        counts[f["severity"]] += 1

    print("\n" + "=" * 70)
    print("  IAM EVIDENCE VALIDATOR — FINDINGS SUMMARY")
    print("=" * 70)
    print(f"  HR records checked   : {hr_count}")
    print(f"  LDAP accounts found  : {ldap_count}")
    print(f"  Total findings       : {len(findings)}")
    print("-" * 70)
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        icon = SEVERITY_ICONS[sev]
        print(f"  {icon}  {sev:<10} : {counts[sev]}")
    print("=" * 70)

    if not findings:
        print("\n  ✅  No findings. HR source and LDAP directory are in sync.\n")
        return

    sorted_findings = sorted(findings, key=lambda f: SEVERITY_ORDER[f["severity"]])

    print("\n  FINDINGS\n")
    for i, f in enumerate(sorted_findings, 1):
        icon = SEVERITY_ICONS[f["severity"]]
        print(f"  [{i:02d}] {icon} {f['severity']} — {f['title']}")
        print(f"       empid      : {f['empid']}")
        print(f"       control    : {f['control']}")
        print(f"       detail     : {f['detail']}")
        print(f"       remediation: {f['remediation']}")
        print()


def write_json_report(
    findings: list[dict],
    hr_count: int,
    ldap_count: int,
    output_dir: str = ".",
) -> str:
    """Write structured findings to a timestamped JSON file."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = os.path.join(output_dir, f"findings_{ts}.json")

    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        counts[f["severity"]] += 1

    report = {
        "report_metadata": {
            "generated_at":     datetime.now(timezone.utc).isoformat(),
            "generated_by":     "iam_evidence_validator.py",
            "hr_source":        HR_CSV_PATH,
            "ldap_host":        LDAP_HOST,
            "base_dn":          BASE_DN,
            "hr_records_count": hr_count,
            "ldap_accounts_count": ldap_count,
            "total_findings":   len(findings),
        },
        "finding_summary": counts,
        "grc_control_coverage": {
            "SOC 2 CC6.1": "Logical access controls — orphaned accounts and attribute drift",
            "SOC 2 CC6.2": "Access provisioning — joiner gaps and manager assignment",
            "SOC 2 CC6.3": "Access removal — leaver failures and inactive account state",
        },
        "findings": sorted(
            findings,
            key=lambda f: (SEVERITY_ORDER[f["severity"]], f["empid"]),
        ),
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return filename


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"\n  Loading HR source from: {HR_CSV_PATH}")
    try:
        hr = load_hr_records(HR_CSV_PATH)
    except FileNotFoundError:
        print(f"ERROR: HR CSV not found at {HR_CSV_PATH}")
        print("Set HR_CSV_PATH environment variable to the correct path.")
        sys.exit(1)

    print(f"  Loaded {len(hr)} HR records\n")

    print(f"  Connecting to LDAP at {LDAP_HOST}:{LDAP_PORT} ...")
    try:
        server = Server(LDAP_HOST, port=LDAP_PORT, get_info=ALL)
        conn   = Connection(
            server,
            user=LDAP_BIND_DN,
            password=LDAP_PASSWORD,
            auto_bind=True,
        )
    except LDAPException as e:
        print(f"ERROR: LDAP connection failed — {e}")
        print("Check LDAP_HOST, LDAP_PORT, LDAP_BIND_DN, LDAP_PASSWORD.")
        sys.exit(1)

    print("  Connected successfully\n")
    ldap = load_ldap_accounts(conn)
    conn.unbind()
    print(f"  Found {len(ldap)} LDAP accounts across all OUs\n")

    print("  Running governance checks ...")
    findings = run_checks(hr, ldap)

    print_summary(findings, len(hr), len(ldap))

    output_file = write_json_report(findings, len(hr), len(ldap))
    print(f"  📄 JSON evidence report written to: {output_file}\n")


if __name__ == "__main__":
    main()