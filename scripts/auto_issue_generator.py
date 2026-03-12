#!/usr/bin/env python3
"""
Oraculus DI Auditor - Auto Issue Generator

Creates GitHub issue markdown drafts for high-severity findings from manifests.
Generates local issue files in reports/issues/ directory.

Usage:
    python scripts/auto_issue_generator.py --manifests-dir manifests
    python scripts/auto_issue_generator.py --severity high --severity critical
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class IssueGenerator:
    """Generates issue drafts from audit manifests."""

    def __init__(
        self,
        manifests_dir: str = "manifests",
        issues_dir: str = "reports/issues",
        template_path: str = ".github/ISSUE_TEMPLATE/audit_finding.md",
    ):
        self.manifests_dir = Path(manifests_dir)
        self.issues_dir = Path(issues_dir)
        self.template_path = Path(template_path)
        self.issues_dir.mkdir(parents=True, exist_ok=True)

    def load_manifests(self) -> list[dict[str, Any]]:
        """Load all manifest files."""
        manifests = []

        if not self.manifests_dir.exists():
            return manifests

        for manifest_file in self.manifests_dir.glob("*.json"):
            try:
                with open(manifest_file) as f:
                    manifest = json.load(f)
                    manifest["_file_path"] = str(manifest_file)
                    manifests.append(manifest)
            except Exception as e:
                print(
                    f"Warning: Failed to load manifest {manifest_file}: {e}",
                    file=sys.stderr,
                )

        return manifests

    def filter_by_severity(
        self, manifests: list[dict[str, Any]], severities: list[str]
    ) -> list[dict[str, Any]]:
        """Filter manifests to only those with flags matching severity levels."""
        filtered = []

        for manifest in manifests:
            flags = manifest.get("flags", [])
            matching_flags = [
                f for f in flags if f.get("severity", "").lower() in severities
            ]

            if matching_flags:
                manifest["_matching_flags"] = matching_flags
                filtered.append(manifest)

        return filtered

    def generate_issue_markdown(
        self, manifest: dict[str, Any], flag: dict[str, Any]
    ) -> str:
        """Generate issue markdown from manifest and flag."""
        doc_id = manifest.get("document_id", "UNKNOWN")
        checksum = manifest.get("checksum_sha256", "N/A")
        manifest_path = manifest.get("_file_path", f"manifests/{doc_id}.json")

        # Determine fault line category
        category = flag.get("category", "uncategorized")
        category_checkboxes = {
            "doj_certification": (
                "- [x] DOJ Certification\n"
                "- [ ] IRB Consent (28 C.F.R. Part 46)\n"
                "- [ ] Infrastructure Policy\n"
                "- [ ] Federal Grant Incentives"
            ),
            "irb_consent": (
                "- [ ] DOJ Certification\n"
                "- [x] IRB Consent (28 C.F.R. Part 46)\n"
                "- [ ] Infrastructure Policy\n"
                "- [ ] Federal Grant Incentives"
            ),
            "infrastructure_policy": (
                "- [ ] DOJ Certification\n"
                "- [ ] IRB Consent (28 C.F.R. Part 46)\n"
                "- [x] Infrastructure Policy\n"
                "- [ ] Federal Grant Incentives"
            ),
            "federal_grant_incentives": (
                "- [ ] DOJ Certification\n"
                "- [ ] IRB Consent (28 C.F.R. Part 46)\n"
                "- [ ] Infrastructure Policy\n"
                "- [x] Federal Grant Incentives"
            ),
        }
        category_checkbox = category_checkboxes.get(
            category,
            (
                "- [ ] DOJ Certification\n"
                "- [ ] IRB Consent (28 C.F.R. Part 46)\n"
                "- [ ] Infrastructure Policy\n"
                "- [ ] Federal Grant Incentives"
            ),
        )

        # Severity
        severity = flag.get("severity", "medium").capitalize()

        # Message
        message = flag.get("message", "No description provided")

        # Author and timestamp
        author = flag.get("author", "Unknown")
        timestamp = flag.get("timestamp", datetime.utcnow().isoformat())

        issue_content = f"""---
name: Audit Finding
about: Report an audit finding or compliance issue identified during document review
title: '[AUDIT] {message[:50]}'
labels: audit, compliance, severity-{flag.get("severity", "medium")}
assignees: ''
---

## Audit Finding Details

**Document ID**: {doc_id}

**Manifest Path**: {manifest_path}

**Finding Summary**: {message}

**Severity**: {severity}

**Category (Fault Line)**:
{category_checkbox}

## Evidence

**Document Checksum (SHA-256)**: `{checksum[:16]}...`

**Page/Section Reference**: <!-- Review manifest for details -->

**Excerpt or Description**:
```
{message}
```

## Impact Assessment

**Legal Risk**: {severity}

**Compliance Impact**: See compliance_checklist.md for {category} requirements

**Urgency**: {
    "Immediate"
    if flag.get("severity") in ["high", "critical"]
    else "Standard review timeline"
}

## Recommended Actions

1. Review document and verify finding
2. Consult legal counsel if required
3. Document resolution in manifest
4. Update issue with resolution status

## Additional Context

**Related Documents**: <!-- Add related document IDs if known -->

**Previous Findings**: <!-- Reference related issues -->

**Assigned Reviewer**: <!-- Assign based on category -->

---

## Chain of Custody

- **Reported by**: {author}
- **Date reported**: {timestamp[:10]}
- **Review required by**: <!-- Assign reviewer -->

## Attachments

Manifest file: {manifest_path}

---

**For Repository Maintainers**:
- Verify manifest file is attached or referenced
- Confirm severity and category alignment: {severity} / {category}
- Assign to appropriate legal/compliance reviewer
- Update manifest with issue number once created

**Auto-generated by**: auto_issue_generator.py
**Flag ID**: {flag.get("flag_id", "N/A")}
"""

        return issue_content

    def generate_issues(self, manifests: list[dict[str, Any]]) -> list[Path]:
        """Generate issue files for manifests with matching flags."""
        generated_files = []

        for manifest in manifests:
            doc_id = manifest.get("document_id", "UNKNOWN")
            matching_flags = manifest.get("_matching_flags", [])

            for i, flag in enumerate(matching_flags):
                flag_id = flag.get("flag_id", f"FLAG_{i+1:04d}")

                # Generate issue markdown
                issue_content = self.generate_issue_markdown(manifest, flag)

                # Sanitize filename components to prevent path traversal
                safe_doc_id = "".join(
                    c if c.isalnum() or c in "_-" else "_" for c in doc_id
                )
                safe_flag_id = "".join(
                    c if c.isalnum() or c in "_-" else "_" for c in flag_id
                )

                # Save to file
                issue_filename = f"{safe_doc_id}_{safe_flag_id}.md"
                issue_path = self.issues_dir / issue_filename

                with open(issue_path, "w") as f:
                    f.write(issue_content)

                generated_files.append(issue_path)

        return generated_files


def main():
    parser = argparse.ArgumentParser(
        description="Oraculus DI Auditor - Auto Issue Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate issues for all high and critical findings
  python scripts/auto_issue_generator.py --severity high --severity critical

  # Generate issues from specific manifests directory
  python scripts/auto_issue_generator.py --manifests-dir manifests \\
      --output reports/issues
        """,
    )

    parser.add_argument(
        "--manifests-dir",
        type=str,
        default="manifests",
        help="Directory containing manifest files",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/issues",
        help="Output directory for issue files",
    )
    parser.add_argument(
        "--severity",
        type=str,
        action="append",
        default=[],
        help="Filter by severity (can specify multiple times)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate issues for all severities",
    )

    args = parser.parse_args()

    # Determine severity filter
    if args.all:
        severities = ["low", "medium", "high", "critical"]
    elif args.severity:
        severities = [s.lower() for s in args.severity]
    else:
        # Default to high and critical only
        severities = ["high", "critical"]

    print("Oraculus DI Auditor - Auto Issue Generator")
    print(f"  Manifests: {args.manifests_dir}")
    print(f"  Output: {args.output}")
    print(f"  Severity filter: {', '.join(severities)}")

    # Initialize generator
    generator = IssueGenerator(manifests_dir=args.manifests_dir, issues_dir=args.output)

    # Load manifests
    print("\nLoading manifests...")
    manifests = generator.load_manifests()
    print(f"  Loaded {len(manifests)} manifest(s)")

    if not manifests:
        print("No manifests found. Nothing to generate.")
        sys.exit(0)

    # Filter by severity
    filtered_manifests = generator.filter_by_severity(manifests, severities)
    print(f"  Found {len(filtered_manifests)} manifest(s) with matching flags")

    if not filtered_manifests:
        print("No manifests with matching severity levels. Nothing to generate.")
        sys.exit(0)

    # Generate issues
    print("\nGenerating issue files...")
    generated_files = generator.generate_issues(filtered_manifests)

    print(f"\n✓ Generated {len(generated_files)} issue file(s)")
    for issue_file in generated_files:
        print(f"  - {issue_file}")

    print("\nNext steps:")
    print(f"  1. Review issue files in {args.output}")
    print("  2. Manually create GitHub issues from these drafts")
    print("  3. Update manifests with issue numbers once created")


if __name__ == "__main__":
    main()
