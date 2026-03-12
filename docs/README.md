# Oraculus DI Auditor Documentation

This directory contains project documentation for the Oraculus DI Auditor platform.

## Architecture Overview

The Oraculus DI Auditor is structured as a modular Python application with the following components:

### Core Packages

- **`core/`** - Fundamental abstractions, base classes, and utilities used throughout the application. Provides the foundation for the audit framework.

- **`io/`** - Input/Output operations for data ingestion and export. Handles:
  - Schema validation and loading from `schemas/`
  - Configuration management from `config/`
  - Data source connectors and integrations
  - Report generation and export

- **`models/`** - Data models and domain entities representing:
  - Audit definitions and rules
  - Audit findings and results
  - Reporting structures and metadata

- **`pipelines/`** - Audit pipeline orchestration and workflow management:
  - Pipeline stages for audit execution
  - Data processing and validation
  - Report generation workflows

### Supporting Directories

- **`schemas/`** - JSON Schema definitions for data validation
- **`config/`** - Configuration files for audit rules and system settings
- **`data/`** - Runtime data directory (excluded from git via .gitignore)
- **`tests/`** - Test suite for all components

## Development

See the main [README.md](../README.md) for development setup and contribution guidelines.
