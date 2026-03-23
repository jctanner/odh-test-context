# Test Context: org-management

**Repository**: opendatahub-io/org-management
**Type**: Configuration-as-Code (YAML + Python validation)
**Languages**: YAML, Python
**Agent Readiness**: **HIGH** - All validation commands work in container, clear pass/fail signals

## Overview

This repository manages GitHub organization membership for opendatahub-io using Peribolos. It contains YAML configuration files defining org members and admins, with Python validation scripts that enforce data integrity rules. There are no traditional unit tests - validation consists of linting YAML files and running 4 Python checks to ensure config correctness.

**What an agent can validate**:
- YAML syntax and formatting (yamllint)
- Alphabetical ordering of user lists
- No duplicate users in lists
- No overlap between admins and members
- No admins key in members file

**Limitations**:
- Cannot test the Peribolos apply workflow (requires GitHub token and org access)
- Validation scripts are inline in GitHub Actions (not standalone files)

---

## Container Recipe

This is the complete, copy-paste recipe for validating patches in a container.

### 1. Start Container

```bash
podman run -d --name test-context-org-management \
  -v $(pwd):/app:Z \
  -w /app \
  python:3.11 \
  sleep infinity
```

Or with docker:
```bash
docker run -d --name test-context-org-management \
  -v $(pwd):/app \
  -w /app \
  python:3.11 \
  sleep infinity
```

### 2. Install Dependencies

```bash
podman exec test-context-org-management bash -c "pip install pyyaml yamllint"
```

Expected output: `Successfully installed pathspec-1.0.4 pyyaml-6.0.3 yamllint-1.38.0`

### 3. Run Lint

```bash
podman exec test-context-org-management bash -c "cd /app && yamllint ."
```

**Expected**: Exit code 0, possibly with warnings about truthy values (non-blocking)

### 4. Run Validation Checks

#### Check 1: User Order (Alphabetical)

```bash
podman exec test-context-org-management bash -c "cd /app && python3 -c \"
import yaml

def is_list_sorted(data):
    return all(data[i].lower() <= data[i + 1].lower() for i in range(len(data) - 1))

with open('config/organization_members.yaml') as f:
    data = yaml.safe_load(f)
orgs = data['orgs'].keys()
for org in orgs:
    org_owners = data['orgs'][org].get('admins', [])
    org_members = data['orgs'][org].get('members', [])

    if not is_list_sorted(org_owners):
        print(f'The list of owners for org {org} is not in alphabetical order!')
        exit(1)
    elif not is_list_sorted(org_members):
        print(f'The list of members for org {org} is not in alphabetical order!')
        exit(1)
print('✓ User order check passed')
\""
```

**Expected**: `✓ User order check passed` (exit code 0)

#### Check 2: No Overlap Between Admins and Members

```bash
podman exec test-context-org-management bash -c "cd /app && python3 -c \"
import yaml

with open('config/organization_members.yaml') as f:
    members_data = yaml.safe_load(f)
with open('config/organization_admins.yaml') as f:
    owners_data = yaml.safe_load(f)
orgs = members_data['orgs'].keys()
for org in orgs:
    org_owners = owners_data['orgs'][org].get('admins', [])
    org_members = members_data['orgs'][org].get('members', [])

    if len(set(org_owners).intersection(org_members)) > 0:
        print(f'There is a user listed in members that is also listed in owners for org {org}')
        exit(1)
print('✓ No overlap between owners and members')
\""
```

**Expected**: `✓ No overlap between owners and members` (exit code 0)

#### Check 3: No Duplicate Users

```bash
podman exec test-context-org-management bash -c "cd /app && python3 -c \"
import yaml

with open('config/organization_members.yaml') as f:
    data = yaml.safe_load(f)
orgs = data['orgs'].keys()
for org in orgs:
    org_owners = data['orgs'][org].get('admins', [])
    org_members = data['orgs'][org].get('members', [])

    if len(set(org_owners)) < len(org_owners):
        print(f'There is a duplicate user in the list of owners for org {org}')
        exit(1)
    if len(set(org_members)) < len(org_members):
        print(f'There is a duplicate user in the list of members for org {org}')
        exit(1)
print('✓ No duplicate users found')
\""
```

**Expected**: `✓ No duplicate users found` (exit code 0)

#### Check 4: No Admins in Members File

```bash
podman exec test-context-org-management bash -c "cd /app && python3 -c \"
import yaml

with open('config/organization_members.yaml') as f:
    data = yaml.safe_load(f)
orgs = data['orgs'].keys()
for org in orgs:
    if 'admins' in data['orgs'][org].keys():
        print('Changes to the org membership that change the list of owners are not allowed.')
        exit(1)
print('✓ No admins in members file')
\""
```

**Expected**: `✓ No admins in members file` (exit code 0)

### 5. Cleanup

```bash
podman rm -f test-context-org-management
```

---

## Validation Results

All commands validated successfully in Python 3.11 container:

| Step | Command | Result | Notes |
|------|---------|--------|-------|
| Install | `pip install pyyaml yamllint` | ✓ PASS | Installed pyyaml-6.0.3, yamllint-1.38.0 |
| Lint | `yamllint .` | ✓ PASS | 2 warnings (truthy values), exit code 0 |
| Test 1 | User order check | ✓ PASS | All users alphabetical |
| Test 2 | Overlap check | ✓ PASS | No users in both lists |
| Test 3 | Duplicates check | ✓ PASS | No duplicates found |
| Test 4 | Admins check | ✓ PASS | No admins key in members file |

**All validation checks passed.** An agent can apply patches and get clear pass/fail signals.

---

## CI/CD

**System**: GitHub Actions
**Config**: `.github/workflows/verify-pull-requests.yaml`

### Gating Checks (Required for PR Merge)

All checks in the "Verify Pull Requests" workflow are gating:

1. **yamllint** - Lints all YAML files using karancode/yamllint-github-action@master
   ```yaml
   - uses: karancode/yamllint-github-action@master
     with:
       yamllint_comment: true
   ```

2. **Check user order** - Verifies users are alphabetically sorted
   - Runs inline Python script with `jannekem/run-python-script-action@v1`
   - Checks both admins and members lists
   - Exits with code 1 if not sorted

3. **Check for overlap** - Ensures no user is in both admins and members
   - Loads both `organization_admins.yaml` and `organization_members.yaml`
   - Checks for intersection between admin and member sets
   - Exits with code 1 if overlap found

4. **Check for duplicates** - Ensures no duplicate users in any list
   - Checks if set length < list length for both admins and members
   - Exits with code 1 if duplicates found

5. **Ensure admins not set** - Prevents changes to admins via members file
   - Verifies `admins` key does not exist in `organization_members.yaml`
   - Exits with code 1 if admins key present

### Post-Merge Workflow

**Apply Organization Membership** (`.github/workflows/apply-org-membership.yaml`):
- Triggers on push to main when `config/organization_members.yaml` changes
- Merges admin and member configs
- Runs Peribolos tool to sync GitHub org membership
- **Cannot be validated locally** - requires `ORG_MANAGEMENT_TOKEN` secret and org admin access

---

## Conventions

### File Structure

```
config/
  organization_admins.yaml  - Defines org admins (protected)
  organization_members.yaml - Defines org members (editable)
```

### User List Format

```yaml
orgs:
  opendatahub-io:
    members:
      - alice
      - bob
      - charlie
```

**Rules**:
- Users must be in alphabetical order (case-insensitive)
- No duplicates allowed
- No user can be in both admins and members
- The `admins` key must NOT appear in `organization_members.yaml`

### Adding a New Member

1. Edit `config/organization_members.yaml`
2. Add GitHub username to `members` list in alphabetical order
3. Run validation checks to verify
4. Submit PR - all checks must pass

---

## Gaps & Caveats

1. **No standalone test script** - Validation logic is embedded in GitHub Actions YAML. To run locally, you must copy the inline Python scripts.

2. **No yamllint config file** - Linter runs with defaults. The repo has 2 warnings about truthy values in workflow files that are accepted.

3. **Cannot test Peribolos** - The apply workflow requires GitHub org admin token and actual org access. Can only validate config format, not the apply behavior.

4. **No pre-commit hooks** - Validation only runs in CI, not on local commits.

5. **No traditional test framework** - This is a config repo with validation checks, not a software project with unit tests.

6. **Python version not pinned** - CI uses `python-version: '3.x'`, actual version varies. Container validation used Python 3.11.

---

## Quick Reference

**Add this repo to an agent's validation pipeline**:

```bash
# Clone and validate
git clone <repo>
cd org-management

# Run in container
podman run -d --name validate-org \
  -v $(pwd):/app:Z -w /app python:3.11 sleep infinity
podman exec validate-org pip install pyyaml yamllint
podman exec validate-org yamllint .
podman exec validate-org python3 -c "<user order check>"
podman exec validate-org python3 -c "<overlap check>"
podman exec validate-org python3 -c "<duplicates check>"
podman exec validate-org python3 -c "<admins check>"
podman rm -f validate-org
```

**Exit codes**:
- 0 = All checks passed
- 1 = Validation failed (lint errors, user order wrong, duplicates, overlap, or admins present)

**Agent readiness: HIGH** - Complete validation possible in isolated container with clear pass/fail signals.
