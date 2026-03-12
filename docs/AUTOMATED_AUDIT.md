# Automated Repository Audit

## Overview

The `automated_audit.py` script provides comprehensive automated repository analysis and triage. It scans all files, directories, and code in the repository to automatically identify notable artifacts, flags, issues, and configurations based on conventional audit criteria.

## Features

### Audit Categories

1. **Code Quality Analysis**
   - Missing docstrings (module, class, function level)
   - Cyclomatic complexity detection
   - TODO/FIXME comment tracking
   - Large file detection (>1000 lines)
   - Bare except clause detection
   - Print statement counting (debug code detection)

2. **Documentation Assessment**
   - Short documentation detection
   - Broken link checking
   - Outdated year reference detection
   - Required file verification (README, LICENSE, etc.)

3. **Configuration Auditing**
   - Hardcoded credentials/secrets detection
   - Debug mode checks
   - JSON/YAML validation
   - Unpinned dependency detection

4. **Security Scanning**
   - Hardcoded password patterns
   - API key detection
   - AWS credentials detection
   - Private key detection
   - SQL injection vulnerability patterns

5. **Data Privacy**
   - PII field detection in JSON data
   - Email, phone, SSN pattern detection
   - Address and credit card field identification

6. **Test Coverage**
   - Test-to-source file ratio calculation
   - Test file identification

7. **Compliance & Structure**
   - File type distribution analysis
   - Repository size metrics
   - Large file flagging (>1MB)

## Usage

### Basic Usage

Run the audit from the repository root:

```bash
python3 scripts/automated_audit.py
```

The script will:
1. Scan all files and directories (excluding common build/cache directories)
2. Analyze each file based on its type
3. Generate a comprehensive audit report
4. Save the report as `AUDIT_REPORT.txt` in the repository root

### Output

The generated `AUDIT_REPORT.txt` contains four main sections:

1. **Repository Overview**
   - Total file and directory counts
   - Python, test, config, and documentation file counts
   - Total lines and code lines
   - File type distribution

2. **Global Flags and Issues**
   - High-level repository-wide concerns
   - Missing required files
   - Security issue summaries
   - Test coverage metrics

3. **File-by-File Findings**
   - Detailed findings for each file with issues
   - Issues (critical problems)
   - Warnings (potential problems)
   - Notes (informational items)

4. **Recommendations**
   - Actionable suggestions for improvement
   - Prioritized by impact

## Interpretation Guide

### Severity Levels

- **Issues**: Critical problems that should be addressed (e.g., syntax errors, hardcoded secrets)
- **Warnings**: Potential problems that warrant review (e.g., missing docstrings, complexity)
- **Notes**: Informational items for awareness (e.g., TODO comments, print statements)

### Global Flags

- **HIGH**: Immediate attention required (security issues)
- **MEDIUM**: Should be addressed soon (missing documentation)
- **LOW**: Nice to have (large files)
- **INFO**: Informational summary

## Customization

### Excluding Directories

The script automatically skips these patterns:
- `.git`
- `__pycache__`
- `node_modules`
- `.venv`, `venv`
- `.pytest_cache`
- `dist`, `build`
- `*.egg-info`
- `.mypy_cache`
- `.ruff_cache`

To add more patterns, edit the `skip_patterns` set in the `RepositoryAuditor` class.

### Adjusting Thresholds

Key thresholds can be adjusted:
- Large file threshold: 1000 lines (see `analyze_python_file`)
- Complex function threshold: 10 control flow nodes (see `analyze_python_ast`)
- Large data file threshold: 1MB (see `analyze_data_file`)
- Test coverage ratio: 30% minimum (see `generate_global_flags`)

## Integration

### CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
- name: Run Automated Audit
  run: python3 scripts/automated_audit.py

- name: Upload Audit Report
  uses: actions/upload-artifact@v3
  with:
    name: audit-report
    path: AUDIT_REPORT.txt
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: automated-audit
      name: Repository Audit
      entry: python3 scripts/automated_audit.py
      language: system
      pass_filenames: false
      always_run: true
```

## Reproducibility

The audit script is deterministic and will produce identical results for identical repository states. All findings are based on static analysis patterns and do not depend on external services or random processes.

## Limitations

This automated audit tool:

- Performs **static analysis only** - does not execute code
- May produce **false positives** - manual review recommended
- Does **not replace** manual code review or security audits
- Is **language-specific** - optimized for Python, with basic support for other languages
- Cannot detect **runtime issues** - only analyzes source code structure

## Security Note

The script attempts to identify hardcoded secrets and credentials, but:

- It may miss sophisticated obfuscation techniques
- It may produce false positives for legitimate patterns
- It does not guarantee finding all security issues
- Professional security audits are still recommended for production systems

## Maintenance

The audit script is self-contained and requires only Python 3.11+ standard library. No external dependencies are needed for basic operation.

## Examples

### Example Output

```
================================================================================
AUTOMATED REPOSITORY AUDIT REPORT
================================================================================

Generated: 2026-01-15T22:50:08.942980Z
Repository: Oraculus-DI-Auditor
Repository Path: /home/runner/work/Oraculus-DI-Auditor/Oraculus-DI-Auditor

================================================================================
REPOSITORY OVERVIEW
================================================================================

Total Directories: 201
Total Files: 661
Python Files: 361
Test Files: 114
Configuration Files: 2
Documentation Files: 99
Total Lines: 132,089
Code Lines: 77,502

File Types Distribution:
  .py                 :   361
  .json               :   155
  .md                 :    93
  ...

================================================================================
GLOBAL FLAGS AND ISSUES
================================================================================

[MEDIUM] [DOCUMENTATION] Missing LICENSE
[INFO] [SUMMARY] Total issues: 3
[INFO] [SUMMARY] Total warnings: 237
...
```

## Support

For issues or questions about the automated audit script:
1. Check the audit report for specific findings
2. Review this documentation for interpretation guidance
3. Open an issue in the repository with the `audit` label

## Version History

- **v1.0.0** (2026-01-15): Initial release with comprehensive audit capabilities
