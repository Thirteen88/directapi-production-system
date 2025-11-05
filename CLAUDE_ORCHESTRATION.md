# Claude Orchestration Master Rules

**Version:** 1.0.0
**Last Updated:** 2025-10-23
**Status:** Production-Ready

---

## 1. Purpose and Scope

### 1.1 Overall Objectives

This document defines the canonical rules for **reduce-and-delegate orchestration** using Claude Code. The orchestration pattern enables:

- **Decomposition** of complex tasks into manageable sub-tasks
- **Parallel execution** of independent work streams via sub-agents
- **Context management** to stay within token budgets
- **Reproducible workflows** with audit trails and versioning
- **Scalable agent coordination** for large-scale code analysis, refactoring, and generation

### 1.2 Roles and Responsibilities

#### Orchestrator Agent (Primary)
- Receives high-level user requests
- Analyzes task complexity and determines decomposition strategy
- Spawns sub-agents with precise, isolated prompts
- Aggregates sub-agent outputs
- Resolves conflicts and synthesizes final deliverables
- Maintains audit trail and version history

#### Sub-Agent (Delegated)
- Receives scoped, self-contained task definition
- Executes within defined boundaries (file scope, module scope, etc.)
- Returns structured output in specified format
- Operates independently without cross-agent communication
- Reports errors/blockers without attempting global decisions

#### User
- Provides initial high-level request
- Reviews orchestrator's decomposition plan before execution
- Approves delegation strategy and resource allocation
- Receives final aggregated output with audit trail

---

## 2. Context Management

### 2.1 Token Budget Allocation

**Total Budget:** 200,000 tokens (Claude Sonnet 4.5 limit)

**Allocation Strategy:**
- **Orchestrator overhead:** 20,000 tokens (10%)
  - Task analysis and planning
  - Coordination logic
  - Output aggregation
- **Sub-agent budget pool:** 160,000 tokens (80%)
  - Divided equally among planned sub-agents
  - Minimum 10,000 tokens per sub-agent
  - Maximum 12 concurrent sub-agents
- **Safety buffer:** 20,000 tokens (10%)
  - Error handling and retries
  - Final synthesis and reporting

### 2.2 Context Pruning Rules

**When to Prune:**
- Orchestrator context exceeds 15,000 tokens
- Sub-agent delegation history grows beyond 5 completed tasks
- Intermediate outputs exceed 30,000 tokens combined

**What to Prune:**
1. **Historical sub-agent prompts** (retain only last 3)
2. **Verbose tool outputs** (summarize file contents, compress logs)
3. **Redundant analysis** (cache and reference instead of repeating)
4. **User conversational context** (retain task spec only)

**What to Retain:**
1. **Active task specification** (user's original request)
2. **Current delegation plan** (task breakdown, assignments)
3. **Sub-agent outputs** (structured results, not full logs)
4. **Error states and blockers** (for retry logic)
5. **Audit trail metadata** (version, timestamp, agent IDs)

### 2.3 Retention Windows

- **Task specification:** Entire session
- **Delegation plan:** Until final output delivered
- **Sub-agent outputs:** 24 hours or until aggregation complete
- **Error logs:** 7 days
- **Audit trails:** Permanent (written to disk)

---

## 3. Reduction Rules

### 3.1 When to Break Tasks Into Sub-Tasks

**Trigger Conditions (any true):**
1. **File count > 10:** Task involves analyzing or modifying more than 10 files
2. **Module boundaries:** Task spans multiple logical modules/packages
3. **Independent work streams:** Task contains 3+ parallelizable sub-tasks
4. **Token forecast > 80,000:** Estimated context consumption exceeds 40% of budget
5. **Time estimate > 15 minutes:** Task execution time exceeds orchestrator efficiency threshold

**Examples:**
- **Trigger:** "Refactor authentication across 25 files" → File count > 10 ✓
- **Trigger:** "Add logging to API, database, and UI layers" → Module boundaries ✓
- **No trigger:** "Fix typo in README.md" → Single file, simple task

### 3.2 How to Decompose Tasks

**Decomposition Strategies:**

#### Strategy 1: File-Based Decomposition
- **When:** Task involves independent operations on multiple files
- **Method:** One sub-agent per file or small file group (3-5 files)
- **Example:** "Update imports across 20 components" → 4 sub-agents (5 files each)

#### Strategy 2: Module-Based Decomposition
- **When:** Task spans logical architecture boundaries
- **Method:** One sub-agent per module/package
- **Example:** "Add error handling to backend, frontend, shared utils" → 3 sub-agents

#### Strategy 3: Phase-Based Decomposition
- **When:** Task has sequential dependencies but parallelizable phases
- **Method:** One sub-agent per phase, orchestrator chains outputs
- **Example:** "Analyze codebase → Generate plan → Implement changes" → 3 sequential sub-agents

#### Strategy 4: Pattern-Based Decomposition
- **When:** Task applies same operation to multiple patterns
- **Method:** One sub-agent per pattern type
- **Example:** "Migrate all class components to hooks" → 1 sub-agent per component pattern

### 3.3 Decomposition Constraints

**Hard Limits:**
- **Maximum sub-agents:** 12 per orchestration session
- **Minimum task scope:** Each sub-task must be independently executable
- **No circular dependencies:** Sub-agent outputs cannot depend on each other's results
- **Clear success criteria:** Each sub-task must have measurable completion state

**Anti-Patterns to Avoid:**
- **Over-fragmentation:** Creating 50+ micro-tasks for a 20-file refactor
- **Under-specification:** Sub-agent prompt lacks sufficient context
- **Hidden dependencies:** Sub-agent A needs output from B but not declared
- **Scope creep:** Sub-agent prompt allows unbounded exploration

---

## 4. Delegation Rules

### 4.1 Criteria to Spawn Sub-Agents

**Pre-Flight Checklist:**
- [ ] Task decomposition plan documented
- [ ] User approved delegation strategy
- [ ] Token budget allocated per sub-agent
- [ ] Success criteria defined for each sub-task
- [ ] Output format specified (JSON schema)
- [ ] Error handling strategy defined
- [ ] No circular dependencies between sub-tasks

**Spawning Decision Matrix:**

| Task Complexity | File Count | Module Count | Decision |
|-----------------|------------|--------------|----------|
| Low | 1-3 | 1 | Direct execution (no delegation) |
| Medium | 4-10 | 1-2 | Optional delegation (efficiency gain) |
| High | 11-30 | 3-5 | **Recommended delegation** |
| Very High | 31+ | 6+ | **Required delegation** |

### 4.2 Sub-Agent Prompt Protocol

**Standard Structure (JSON Schema):**

```json
{
  "task_id": "unique-identifier-timestamp",
  "agent_role": "Descriptive role (e.g., 'File Analyzer', 'Code Refactorer')",
  "objective": "Single sentence stating what to accomplish",
  "scope": {
    "files": ["absolute/path/to/file1.ts", "absolute/path/to/file2.ts"],
    "directories": ["absolute/path/to/dir"],
    "boundaries": "What NOT to touch or analyze"
  },
  "context": {
    "background": "Minimal context from orchestrator (user's original request)",
    "constraints": ["Constraint 1", "Constraint 2"],
    "dependencies": "Reference to other sub-agent outputs if applicable"
  },
  "instructions": [
    "Step 1: Detailed instruction",
    "Step 2: Next action",
    "Step 3: Final action"
  ],
  "output_format": {
    "type": "json",
    "schema": {
      "results": "Array of results",
      "errors": "Array of errors encountered",
      "metadata": {
        "files_processed": "number",
        "timestamp": "ISO 8601 string"
      }
    }
  },
  "success_criteria": [
    "All files in scope analyzed",
    "Output JSON valid against schema",
    "No unhandled errors"
  ],
  "error_handling": {
    "on_file_not_found": "Log error and continue",
    "on_parse_error": "Log file path and error, skip file",
    "on_permission_denied": "Log and report to orchestrator"
  },
  "token_budget": 15000,
  "timeout": "10 minutes"
}
```

**Prompt Template Text:**

```
You are a specialized sub-agent with the role: {agent_role}

TASK ID: {task_id}
OBJECTIVE: {objective}

SCOPE:
- Files to process: {scope.files}
- Directories: {scope.directories}
- DO NOT modify or analyze: {scope.boundaries}

CONTEXT:
{context.background}

CONSTRAINTS:
{context.constraints}

INSTRUCTIONS:
{instructions}

OUTPUT FORMAT:
Return your results as a JSON object matching this schema:
{output_format.schema}

SUCCESS CRITERIA:
{success_criteria}

ERROR HANDLING:
{error_handling}

TOKEN BUDGET: {token_budget} tokens
TIMEOUT: {timeout}

Begin execution now. Return only the JSON output, no additional commentary.
```

### 4.3 Output Format Requirements

**All sub-agents MUST return:**

```json
{
  "task_id": "echo back the task_id",
  "status": "success | partial_success | failure",
  "results": {
    "summary": "One sentence summary of what was accomplished",
    "details": "Structure varies by task type",
    "files_modified": ["list", "of", "absolute", "paths"],
    "files_analyzed": ["list", "of", "absolute", "paths"]
  },
  "errors": [
    {
      "file": "absolute/path/to/file",
      "error_type": "parse_error | file_not_found | permission_denied",
      "message": "Human-readable error description",
      "recoverable": true
    }
  ],
  "metadata": {
    "agent_role": "echo back the role",
    "timestamp": "2025-10-23T14:32:00Z",
    "execution_time_seconds": 45,
    "tokens_consumed": 12500
  },
  "recommendations": [
    "Optional: Suggestions for orchestrator (e.g., 'Re-run with additional context')"
  ]
}
```

---

## 5. Coordination Protocol

### 5.1 Sub-Agent Output Aggregation

**Orchestrator Responsibilities:**

1. **Collect all outputs** into a structured array
2. **Validate against schemas** (reject malformed responses)
3. **Merge results** based on task type:
   - **File-based tasks:** Consolidate file lists, deduplicate
   - **Analysis tasks:** Merge findings, group by severity/category
   - **Refactoring tasks:** Verify no conflicting changes to same files
4. **Generate summary report** for user

**Aggregation Template:**

```json
{
  "orchestration_id": "unique-orchestration-id",
  "user_request": "Original user request",
  "delegation_plan": {
    "total_sub_agents": 5,
    "decomposition_strategy": "file-based",
    "execution_mode": "parallel"
  },
  "sub_agent_outputs": [
    {
      "task_id": "sub-task-1",
      "agent_role": "File Analyzer",
      "status": "success",
      "output": { /* sub-agent JSON */ }
    }
  ],
  "aggregated_results": {
    "total_files_processed": 45,
    "total_errors": 3,
    "summary": "High-level summary of all sub-agent work",
    "combined_recommendations": []
  },
  "conflicts": [
    {
      "type": "file_modification_conflict",
      "description": "Sub-agent 1 and 3 both modified file.ts",
      "resolution": "Manual review required"
    }
  ],
  "timestamp": "2025-10-23T15:00:00Z",
  "total_execution_time_seconds": 120
}
```

### 5.2 Conflict Resolution

**Conflict Types and Resolution Strategies:**

#### File Modification Conflicts
- **Detection:** Two sub-agents report same file in `files_modified`
- **Resolution:**
  1. Compare modification intents from task specs
  2. If non-overlapping (different lines), attempt merge
  3. If overlapping, escalate to user for manual resolution
  4. Log conflict in audit trail

#### Contradictory Analysis Results
- **Detection:** Sub-agents report conflicting findings (e.g., "security issue" vs "no issues")
- **Resolution:**
  1. Re-run both sub-agents with expanded context
  2. If still conflicting, present both findings to user
  3. Mark as "requires human judgment" in final report

#### Scope Boundary Violations
- **Detection:** Sub-agent modified files outside its scope
- **Resolution:**
  1. Revert unauthorized changes
  2. Re-run sub-agent with stricter boundaries
  3. Log violation for review

#### Resource Exhaustion
- **Detection:** Sub-agent exceeds token budget or timeout
- **Resolution:**
  1. Terminate sub-agent gracefully
  2. Mark task as `partial_success`
  3. Orchestrator decides: retry with reduced scope or escalate to user

### 5.3 Synthesis and Final Delivery

**Final Output Structure:**

```markdown
# Orchestration Results: {User Request}

## Summary
{One paragraph summarizing all work completed}

## Execution Overview
- **Total Sub-Agents:** {count}
- **Successful:** {count}
- **Partial Success:** {count}
- **Failed:** {count}
- **Total Execution Time:** {seconds}s

## Detailed Results

### Sub-Agent 1: {Role}
**Status:** {status}
**Files Processed:** {count}
**Key Findings:**
- {finding 1}
- {finding 2}

### Sub-Agent 2: {Role}
...

## Aggregated Insights
{Cross-cutting insights that span multiple sub-agents}

## Errors and Issues
{Consolidated error list with severity}

## Conflicts Detected
{Any conflicts requiring manual resolution}

## Recommendations
{Orchestrator's suggestions for next steps}

## Audit Trail
- **Orchestration ID:** {id}
- **Timestamp:** {timestamp}
- **Audit Log:** {absolute_path_to_audit_log}
```

---

## 6. Safety and Compliance

### 6.1 Data Handling

**Principles:**
- **No PII in prompts:** Strip sensitive data before delegating to sub-agents
- **No credentials in outputs:** Redact API keys, passwords, tokens from results
- **No external network calls:** Sub-agents operate only on local filesystem
- **No destructive operations without confirmation:** All file modifications require user approval before execution

**Implementation:**
1. Orchestrator scans user request for PII/credentials using regex patterns
2. Redacts sensitive data before creating sub-agent prompts
3. Sub-agents output results to memory, not disk (orchestrator writes to disk)
4. All file writes logged to audit trail with checksums

### 6.2 Reproducibility

**Requirements for Deterministic Orchestration:**

1. **Version all inputs:**
   - User request (verbatim)
   - Codebase state (git commit hash or file checksums)
   - Orchestration rules version (this document's version)
   - Claude model version (e.g., `claude-sonnet-4-5-20250929`)

2. **Version all outputs:**
   - Sub-agent outputs (timestamped JSON files)
   - Final aggregated result
   - Audit log

3. **Record all decisions:**
   - Decomposition strategy chosen (with rationale)
   - Token budget allocation
   - Conflict resolutions
   - Error recovery actions

**Reproducibility Checklist:**
- [ ] Git commit hash recorded (or file checksums if not in git repo)
- [ ] User request saved verbatim to audit log
- [ ] Orchestration rules version logged
- [ ] All sub-agent prompts saved to disk
- [ ] All sub-agent outputs saved to disk
- [ ] Final result includes full audit trail reference

### 6.3 Audit Trails

**Audit Log Structure:**

```json
{
  "orchestration_id": "uuid-v4",
  "version": "1.0.0",
  "timestamp_start": "2025-10-23T14:00:00Z",
  "timestamp_end": "2025-10-23T14:05:00Z",
  "user_request": "Original request verbatim",
  "codebase_state": {
    "git_commit": "abc123def456" || null,
    "file_checksums": {
      "file1.ts": "sha256-hash",
      "file2.ts": "sha256-hash"
    }
  },
  "orchestrator_version": "1.2.3",
  "model_version": "claude-sonnet-4-5-20250929",
  "delegation_plan": {
    "strategy": "file-based",
    "sub_agents": [
      {
        "task_id": "task-1",
        "agent_role": "File Analyzer",
        "prompt_file": "absolute/path/to/prompt-task-1.json",
        "output_file": "absolute/path/to/output-task-1.json",
        "status": "success",
        "tokens_consumed": 12000,
        "execution_time_seconds": 45
      }
    ]
  },
  "conflicts": [],
  "errors": [],
  "final_output_file": "absolute/path/to/final-output.md",
  "total_tokens_consumed": 65000,
  "total_execution_time_seconds": 300
}
```

**Audit Log Storage:**
- **Location:** `~/claude-orchestrator/audit-logs/{orchestration_id}.json`
- **Retention:** Permanent (user responsible for cleanup)
- **Indexing:** Orchestrator maintains `audit-index.json` with all orchestration IDs and timestamps

---

## 7. Sub-Agent Prompt Template

### 7.1 Standard Template (JSON)

```json
{
  "task_id": "{{TASK_ID}}",
  "agent_role": "{{AGENT_ROLE}}",
  "objective": "{{OBJECTIVE}}",
  "scope": {
    "files": ["{{FILE_1}}", "{{FILE_2}}"],
    "directories": ["{{DIR_1}}"],
    "boundaries": "{{BOUNDARIES}}"
  },
  "context": {
    "background": "{{BACKGROUND}}",
    "constraints": ["{{CONSTRAINT_1}}", "{{CONSTRAINT_2}}"],
    "dependencies": "{{DEPENDENCIES}}"
  },
  "instructions": [
    "{{INSTRUCTION_1}}",
    "{{INSTRUCTION_2}}",
    "{{INSTRUCTION_3}}"
  ],
  "output_format": {
    "type": "json",
    "schema": {
      "results": "{{RESULTS_STRUCTURE}}",
      "errors": "Array of error objects",
      "metadata": {
        "files_processed": "number",
        "timestamp": "ISO 8601 string"
      }
    }
  },
  "success_criteria": [
    "{{CRITERION_1}}",
    "{{CRITERION_2}}"
  ],
  "error_handling": {
    "on_file_not_found": "{{ACTION}}",
    "on_parse_error": "{{ACTION}}",
    "on_permission_denied": "{{ACTION}}"
  },
  "token_budget": {{TOKEN_BUDGET}},
  "timeout": "{{TIMEOUT}}"
}
```

### 7.2 Template Usage Guide

**Variable Substitution:**

| Variable | Description | Example |
|----------|-------------|---------|
| `{{TASK_ID}}` | Unique identifier (timestamp-based) | `task-20251023-140530-001` |
| `{{AGENT_ROLE}}` | Descriptive role name | `Code Refactoring Agent` |
| `{{OBJECTIVE}}` | Single sentence goal | `Refactor all class components to functional components with hooks` |
| `{{FILE_N}}` | Absolute file paths | `/home/user/project/src/component.tsx` |
| `{{DIR_N}}` | Absolute directory paths | `/home/user/project/src/components` |
| `{{BOUNDARIES}}` | Exclusions | `Do not modify test files or node_modules` |
| `{{BACKGROUND}}` | Minimal context (2-3 sentences) | `User requested migration to React 18 hooks...` |
| `{{CONSTRAINT_N}}` | Hard constraints | `Preserve all existing prop types` |
| `{{DEPENDENCIES}}` | References to other outputs | `Use the analysis results from task-001` |
| `{{INSTRUCTION_N}}` | Step-by-step actions | `1. Read all files in scope 2. Parse React components 3. Transform classes to functions` |
| `{{RESULTS_STRUCTURE}}` | Custom result schema | `{"components_refactored": [], "errors": []}` |
| `{{CRITERION_N}}` | Measurable success condition | `All components pass type checking` |
| `{{ACTION}}` | Error handling behavior | `Log error and continue` |
| `{{TOKEN_BUDGET}}` | Integer token limit | `15000` |
| `{{TIMEOUT}}` | Human-readable duration | `10 minutes` |

**Example Populated Template:**

```json
{
  "task_id": "task-20251023-140530-001",
  "agent_role": "React Component Refactoring Agent",
  "objective": "Refactor class components to functional components with hooks in the authentication module",
  "scope": {
    "files": [
      "/home/gary/project/src/auth/LoginForm.tsx",
      "/home/gary/project/src/auth/SignupForm.tsx",
      "/home/gary/project/src/auth/PasswordReset.tsx"
    ],
    "directories": [],
    "boundaries": "Do not modify test files, config files, or index.ts"
  },
  "context": {
    "background": "User requested migration from React 17 class components to React 18 functional components with hooks. This is part of a larger modernization effort across the codebase.",
    "constraints": [
      "Preserve all existing prop types and interfaces",
      "Maintain current component APIs (no breaking changes)",
      "Use useState and useEffect hooks appropriately"
    ],
    "dependencies": null
  },
  "instructions": [
    "Read all files in scope and parse React class components",
    "For each class component: convert to functional component with appropriate hooks",
    "Replace this.state with useState, componentDidMount/Update with useEffect",
    "Verify all prop types are preserved",
    "Return a structured JSON report of changes made"
  ],
  "output_format": {
    "type": "json",
    "schema": {
      "results": {
        "components_refactored": [
          {
            "file": "absolute path",
            "component_name": "string",
            "changes": ["description of changes"]
          }
        ]
      },
      "errors": [
        {
          "file": "absolute path",
          "error_type": "string",
          "message": "string",
          "recoverable": "boolean"
        }
      ],
      "metadata": {
        "files_processed": "number",
        "timestamp": "ISO 8601 string"
      }
    }
  },
  "success_criteria": [
    "All class components converted to functional components",
    "All files pass TypeScript type checking",
    "No prop type signatures changed"
  ],
  "error_handling": {
    "on_file_not_found": "Log error and report to orchestrator",
    "on_parse_error": "Log file path and error details, skip file, continue",
    "on_permission_denied": "Log and report to orchestrator immediately"
  },
  "token_budget": 15000,
  "timeout": "10 minutes"
}
```

---

## 8. Versioning and Audit

### 8.1 Version Control

**This Document (CLAUDE_ORCHESTRATION.md):**
- **Versioning Scheme:** Semantic versioning (MAJOR.MINOR.PATCH)
  - **MAJOR:** Breaking changes to orchestration protocol
  - **MINOR:** New features, enhanced strategies, additional templates
  - **PATCH:** Bug fixes, clarifications, typo corrections
- **Storage:** Git repository (`~/claude-orchestrator/`)
- **Change Approval:** All changes require rationale documented in changelog

**Orchestrator Code:**
- Must reference this document's version in audit logs
- Breaking changes to code require MAJOR version bump here
- Code and rules must stay synchronized

### 8.2 Changelog

**Format:**

```markdown
## [1.0.0] - 2025-10-23
### Added
- Initial production release
- Complete orchestration protocol
- Sub-agent prompt templates
- Conflict resolution strategies

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A
```

### 8.3 Rationale Tracking

**For Each Rule/Decision in This Document:**

All rules must have traceable rationale. Examples:

| Rule | Rationale |
|------|-----------|
| Max 12 sub-agents | Based on token budget (160k / 12 = 13.3k tokens per agent, above 10k minimum) |
| Token budget 10% buffer | Allows for error handling, retries, and unexpected context growth |
| File count > 10 triggers delegation | Empirical threshold where orchestration overhead < manual execution time |
| Mandatory JSON output format | Ensures machine-readable aggregation, reduces parsing errors |
| No circular dependencies | Prevents deadlocks and undefined execution order |
| Audit logs permanent | Regulatory compliance, debugging, reproducibility requirements |

---

## 9. Examples

### 9.1 Example 1: Large-Scale Code Analysis

**User Request:**
"Analyze all TypeScript files in the project for unused imports and generate a report."

**Orchestrator Analysis:**
- **File count:** 150 TypeScript files
- **Estimated tokens:** ~120,000 (800 tokens/file average)
- **Trigger:** File count > 10 ✓
- **Strategy:** File-based decomposition, 10 sub-agents (15 files each)

**Delegation Plan:**

```json
{
  "orchestration_id": "orch-20251023-150000",
  "strategy": "file-based",
  "sub_agents": [
    {
      "task_id": "task-001",
      "agent_role": "Import Analyzer",
      "files": ["/project/src/components/Button.tsx", "..."],
      "token_budget": 16000
    },
    {
      "task_id": "task-002",
      "agent_role": "Import Analyzer",
      "files": ["/project/src/utils/api.ts", "..."],
      "token_budget": 16000
    }
    // ... 8 more sub-agents
  ]
}
```

**Sub-Agent Prompt (task-001):**

```json
{
  "task_id": "task-001",
  "agent_role": "Import Analyzer",
  "objective": "Identify all unused imports in assigned TypeScript files",
  "scope": {
    "files": [
      "/home/gary/project/src/components/Button.tsx",
      "/home/gary/project/src/components/Input.tsx"
      // ... 13 more files
    ],
    "boundaries": "Do not modify files, only analyze"
  },
  "instructions": [
    "Read each file and parse import statements",
    "Analyze code to determine which imports are actually used",
    "Report any imports that are declared but never referenced",
    "For each unused import, provide file, line number, and import name"
  ],
  "output_format": {
    "type": "json",
    "schema": {
      "results": {
        "unused_imports": [
          {
            "file": "absolute path",
            "line": "number",
            "import_statement": "string",
            "imported_name": "string"
          }
        ]
      },
      "metadata": {
        "files_processed": "number",
        "timestamp": "ISO 8601"
      }
    }
  },
  "success_criteria": ["All files analyzed", "Valid JSON output"],
  "token_budget": 16000
}
```

**Aggregation:**

Orchestrator collects all 10 sub-agent outputs, merges `unused_imports` arrays, generates final report:

```markdown
# Unused Import Analysis Report

## Summary
Analyzed 150 TypeScript files across 10 sub-agents.
Found 47 unused imports across 32 files.

## Detailed Findings

### High-Priority (imports entire unused modules)
- `/project/src/components/Button.tsx:3` - `import { lodash } from 'lodash'`
- `/project/src/utils/api.ts:7` - `import axios from 'axios'`

### Low-Priority (unused named imports from active modules)
- `/project/src/components/Input.tsx:5` - `import { useState, useEffect } from 'react'` (useEffect unused)

## Recommendations
1. Remove all high-priority unused imports (save ~500KB bundle size)
2. Review low-priority imports for potential future use
3. Run automated cleanup with ESLint --fix

## Audit Trail
- Orchestration ID: orch-20251023-150000
- Execution Time: 180 seconds
- Audit Log: ~/claude-orchestrator/audit-logs/orch-20251023-150000.json
```

---

### 9.2 Example 2: Multi-Module Refactoring

**User Request:**
"Add comprehensive error handling with try-catch blocks to all API client methods across backend, frontend, and shared utils."

**Orchestrator Analysis:**
- **Modules:** 3 (backend, frontend, shared)
- **File count:** ~40 files with API methods
- **Trigger:** Module boundaries ✓
- **Strategy:** Module-based decomposition, 3 sub-agents

**Delegation Plan:**

```json
{
  "orchestration_id": "orch-20251023-160000",
  "strategy": "module-based",
  "sub_agents": [
    {
      "task_id": "task-backend-001",
      "agent_role": "Backend Error Handling Refactorer",
      "scope": {
        "directories": ["/project/backend/src/api"],
        "file_pattern": "*.ts"
      },
      "token_budget": 30000
    },
    {
      "task_id": "task-frontend-002",
      "agent_role": "Frontend Error Handling Refactorer",
      "scope": {
        "directories": ["/project/frontend/src/services"],
        "file_pattern": "*.ts"
      },
      "token_budget": 30000
    },
    {
      "task_id": "task-shared-003",
      "agent_role": "Shared Utils Error Handling Refactorer",
      "scope": {
        "directories": ["/project/shared/utils"],
        "file_pattern": "*.ts"
      },
      "token_budget": 20000
    }
  ]
}
```

**Sub-Agent Prompt (task-backend-001):**

```json
{
  "task_id": "task-backend-001",
  "agent_role": "Backend Error Handling Refactorer",
  "objective": "Add comprehensive try-catch error handling to all API client methods in the backend module",
  "scope": {
    "directories": ["/home/gary/project/backend/src/api"],
    "file_pattern": "*.ts",
    "boundaries": "Do not modify test files (*.test.ts, *.spec.ts)"
  },
  "context": {
    "background": "User wants consistent error handling across all API layers. Backend uses custom ApiError class for structured error responses.",
    "constraints": [
      "Use existing ApiError class from @/errors",
      "Preserve existing return types",
      "Log all errors to logger service",
      "Re-throw errors after logging"
    ]
  },
  "instructions": [
    "Find all API client methods (functions that make HTTP requests)",
    "Wrap method bodies in try-catch blocks",
    "In catch block: log error, wrap in ApiError if not already, re-throw",
    "Ensure TypeScript types are preserved",
    "Return list of modified methods with before/after code snippets"
  ],
  "output_format": {
    "type": "json",
    "schema": {
      "results": {
        "methods_modified": [
          {
            "file": "absolute path",
            "method_name": "string",
            "line_number": "number",
            "before_snippet": "string",
            "after_snippet": "string"
          }
        ]
      },
      "metadata": {
        "files_processed": "number",
        "methods_found": "number",
        "methods_modified": "number"
      }
    }
  },
  "success_criteria": [
    "All API methods have try-catch blocks",
    "All errors logged before re-throwing",
    "TypeScript compilation passes"
  ],
  "token_budget": 30000
}
```

**Conflict Detection:**

Orchestrator checks for conflicts:
- **File overlap:** None (each sub-agent works in separate directories)
- **Shared dependencies:** All use `@/errors/ApiError` but don't modify it
- **Style consistency:** All follow same error handling pattern

**Final Output:**

```markdown
# Error Handling Refactoring Report

## Summary
Added comprehensive error handling to 67 API methods across 3 modules.

## Results by Module

### Backend (27 methods modified)
- Files modified: 12
- Pattern: try-catch with ApiError wrapping and logging
- Example: `/backend/src/api/users.ts:getUserById()`

### Frontend (32 methods modified)
- Files modified: 15
- Pattern: try-catch with custom error boundary integration
- Example: `/frontend/src/services/userService.ts:fetchUser()`

### Shared Utils (8 methods modified)
- Files modified: 3
- Pattern: try-catch with generic Error wrapping
- Example: `/shared/utils/httpClient.ts:request()`

## Testing Recommendations
1. Run unit tests for all modified files
2. Test error scenarios (network failures, 404s, 500s)
3. Verify error logging in production environment

## Audit Trail
- Orchestration ID: orch-20251023-160000
- Total Execution Time: 240 seconds
- Audit Log: ~/claude-orchestrator/audit-logs/orch-20251023-160000.json
```

---

### 9.3 Example 3: Sequential Phase Execution

**User Request:**
"Analyze the codebase for security vulnerabilities, generate a remediation plan, then implement high-priority fixes."

**Orchestrator Analysis:**
- **Phases:** 3 sequential (analyze → plan → implement)
- **Dependencies:** Each phase depends on previous output
- **Trigger:** Time estimate > 15 minutes ✓
- **Strategy:** Phase-based decomposition, 3 sequential sub-agents

**Delegation Plan:**

```json
{
  "orchestration_id": "orch-20251023-170000",
  "strategy": "phase-based-sequential",
  "sub_agents": [
    {
      "task_id": "phase-1-analyze",
      "agent_role": "Security Vulnerability Analyzer",
      "execution_order": 1,
      "token_budget": 40000
    },
    {
      "task_id": "phase-2-plan",
      "agent_role": "Remediation Planner",
      "execution_order": 2,
      "depends_on": "phase-1-analyze",
      "token_budget": 25000
    },
    {
      "task_id": "phase-3-implement",
      "agent_role": "Security Fix Implementer",
      "execution_order": 3,
      "depends_on": "phase-2-plan",
      "token_budget": 50000
    }
  ]
}
```

**Execution Flow:**

1. **Phase 1: Analysis**
   - Sub-agent scans codebase for common vulnerabilities (SQL injection, XSS, CSRF, etc.)
   - Outputs: JSON with categorized vulnerabilities and severity ratings

2. **Phase 2: Planning** (uses Phase 1 output)
   - Sub-agent receives vulnerability list
   - Generates remediation plan with prioritization
   - Outputs: JSON with ordered fixes and implementation strategy

3. **Phase 3: Implementation** (uses Phase 2 output)
   - Sub-agent receives remediation plan
   - Implements high-priority fixes only
   - Outputs: JSON with files modified and changes made

**Orchestrator Coordination:**
- Waits for Phase 1 completion before spawning Phase 2
- Passes Phase 1 output as `context.dependencies` to Phase 2 prompt
- Validates each phase output before proceeding
- If any phase fails, halts execution and reports to user

---

## 10. Best Practices

### 10.1 Deterministic Orchestration

**Principles:**
1. **Identical inputs → Identical outputs**
   - Same user request + same codebase state = same result
   - No randomness in decomposition strategy
   - Stable sub-agent ordering

2. **Immutable prompts**
   - Never modify sub-agent prompts after spawning
   - Version all prompt templates
   - Log exact prompt text sent to each sub-agent

3. **Reproducible environment**
   - Lock model version in audit logs
   - Record all tool versions (git, npm, etc.)
   - Capture environment variables affecting execution

**Anti-Patterns:**
- Using timestamps in logic (OK for IDs, not for decisions)
- Non-deterministic file ordering (always sort)
- Relying on filesystem timing/race conditions

### 10.2 Token Budget Management

**Strategies:**

1. **Pre-flight estimation**
   - Calculate estimated tokens before spawning sub-agents
   - Formula: `(avg_file_size_tokens * file_count) + overhead`
   - If estimate > 80% of budget, reduce scope or increase parallelization

2. **Dynamic reallocation**
   - If sub-agent finishes under budget, reallocate to others
   - Monitor token consumption during execution
   - Terminate runaway sub-agents before budget exhaustion

3. **Progressive refinement**
   - Start with high-level analysis (low tokens)
   - Use results to target detailed analysis (high tokens)
   - Avoid analyzing everything at maximum depth

**Example:**
- Total budget: 160,000 tokens
- 8 sub-agents planned
- Initial allocation: 20,000 tokens each
- Sub-agent 1 uses only 12,000 → Reallocate 8,000 to Sub-agent 5 (complex task)

### 10.3 Error Recovery

**Graceful Degradation:**

1. **Sub-agent failure**
   - Mark task as `partial_success` if some files processed
   - Extract usable results from partial output
   - Re-run with reduced scope or expanded timeout

2. **Timeout handling**
   - Capture partial output before timeout
   - Identify bottleneck files (token-heavy)
   - Re-run with bottlenecks excluded or split further

3. **Invalid output**
   - Schema validation catches malformed JSON
   - Request re-run with explicit format examples
   - Fall back to text parsing if JSON fails repeatedly

**Retry Strategy:**
- **Max retries:** 2 per sub-agent
- **Backoff:** Linear (no exponential needed for local execution)
- **Modification:** Reduce scope by 50% on each retry
- **Escalation:** After 2 failures, report to user with detailed error context

### 10.4 Optimization Techniques

**Parallelization:**
- Always prefer parallel execution when tasks are independent
- Use module-based decomposition for architectural boundaries
- Avoid sequential phases unless strictly necessary

**Caching:**
- Cache file reads across sub-agents (orchestrator provides)
- Cache parse results (AST, type info) for large files
- Invalidate cache on file modifications

**Incremental Processing:**
- Process files in batches if total count is very high
- Allow user to review batch 1 results before processing batch 2
- Use results from early batches to refine later batches

**Lazy Loading:**
- Don't read file contents until sub-agent actually needs them
- Provide file lists and metadata first
- Sub-agent requests full content only for relevant files

### 10.5 Communication Patterns

**Orchestrator → User:**
- Always present delegation plan before execution
- Provide progress updates for long-running orchestrations
- Surface errors immediately, don't hide in final report

**Orchestrator → Sub-Agent:**
- Prompts must be self-contained (no assumed context)
- Explicit success criteria, not implicit expectations
- Clear boundaries (what to touch, what to avoid)

**Sub-Agent → Orchestrator:**
- Structured JSON only (no prose unless in designated fields)
- Errors reported with context (file, line, error type)
- Recommendations optional but encouraged

**Anti-Patterns:**
- Sub-agents asking clarifying questions (should be in prompt)
- Orchestrator assuming sub-agent will "figure it out"
- Vague success criteria ("do a good job")

### 10.6 Maintainability

**Documentation:**
- Every decomposition strategy must be documented here
- New sub-agent roles added to template library
- Complex delegation plans saved as examples

**Testing:**
- Test orchestrator with synthetic simple tasks first
- Verify aggregation logic with mock sub-agent outputs
- Regression test: re-run historical orchestrations, compare results

**Monitoring:**
- Track token consumption trends (identify budget creep)
- Monitor sub-agent failure rates by task type
- Analyze execution time vs. file count correlation

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Orchestrator** | Primary agent that decomposes tasks and coordinates sub-agents |
| **Sub-Agent** | Delegated agent executing a scoped, isolated sub-task |
| **Delegation Plan** | Structured breakdown of user request into sub-tasks with assignments |
| **Token Budget** | Maximum tokens allocated to orchestrator or sub-agent |
| **Decomposition Strategy** | Method for breaking tasks (file-based, module-based, phase-based, pattern-based) |
| **Scope** | Files, directories, and boundaries defining sub-agent's work area |
| **Aggregation** | Process of combining sub-agent outputs into cohesive final result |
| **Conflict** | Situation where sub-agents produce contradictory or overlapping results |
| **Audit Trail** | Complete record of orchestration including prompts, outputs, decisions, and metadata |
| **Reduction** | Breaking complex task into simpler sub-tasks |
| **Pruning** | Removing context to stay within token budget |

---

## Appendix B: Quick Reference

### Decision Tree: Should I Delegate?

```
User request received
  ├─ File count ≤ 10 AND single module → Direct execution
  ├─ File count > 10 → Delegate (file-based)
  ├─ Multiple modules → Delegate (module-based)
  ├─ Sequential phases → Delegate (phase-based)
  ├─ Token estimate > 80k → Delegate (any strategy)
  └─ Time estimate > 15 min → Delegate (any strategy)
```

### Token Budget Allocation

| Component | Percentage | Tokens (200k total) |
|-----------|------------|---------------------|
| Orchestrator overhead | 10% | 20,000 |
| Sub-agent pool | 80% | 160,000 |
| Safety buffer | 10% | 20,000 |

### Error Severity Matrix

| Severity | Impact | Orchestrator Action |
|----------|--------|---------------------|
| **Critical** | Entire task blocked | Halt execution, report to user immediately |
| **High** | Sub-agent failed | Retry once, escalate if retry fails |
| **Medium** | Partial results | Mark as `partial_success`, continue |
| **Low** | Individual file error | Log and continue, report in final summary |

### Conflict Types

1. **File modification conflict** → Manual merge or user review
2. **Contradictory analysis** → Present both findings to user
3. **Scope violation** → Revert changes, re-run with stricter boundaries
4. **Resource exhaustion** → Terminate, reallocate tokens, retry with reduced scope

---

## Document Metadata

**Maintained By:** Claude Orchestration Working Group
**Review Cycle:** Quarterly
**Next Review Date:** 2026-01-23
**Feedback:** Submit issues/suggestions to orchestration repository

**Version History:**
- **1.0.0** (2025-10-23): Initial production release

---

**End of Document**
