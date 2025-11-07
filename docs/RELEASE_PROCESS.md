# Release Process

This document describes the automated release process for the Unraid Management Agent Home Assistant integration.

## Overview

The release process is fully automated using GitHub Actions. When you push a version tag (e.g., `v2025.11.1`), the workflow automatically:

1. ✅ Verifies the tag version matches `manifest.json`
2. 📦 Builds the integration package (ZIP file)
3. 🔐 Calculates SHA256 checksum
4. 📝 Extracts release notes from `CHANGELOG.md`
5. 🚀 Creates a GitHub release
6. 📎 Attaches the package and checksum files
7. 🎉 Makes the release available for HACS and manual installation

## Version Naming Convention

Follow the pattern: `v2025.11.x`

- **Format**: `vYYYY.MM.x`
- **Year**: 4-digit year (e.g., `2025`)
- **Month**: 2-digit month (e.g., `11` for November)
- **Patch**: Incrementing number starting from `0` (e.g., `0`, `1`, `2`, ...)

**Examples**:
- `v2025.11.0` - First release in November 2025
- `v2025.11.1` - Second release in November 2025
- `v2025.12.0` - First release in December 2025

**Pre-releases** (optional):
- `v2025.11.1-alpha` - Alpha pre-release
- `v2025.11.1-beta` - Beta pre-release
- `v2025.11.1-rc1` - Release candidate

## Step-by-Step Release Process

### 1. Update the Version

Edit `custom_components/unraid_management_agent/manifest.json`:

```json
{
  "domain": "unraid_management_agent",
  "name": "Unraid Management Agent",
  ...
  "version": "2025.11.1"
}
```

**Important**: The version in `manifest.json` must match the tag you'll create (without the `v` prefix).

### 2. Update the CHANGELOG

Edit `CHANGELOG.md` and add a new section for the release:

```markdown
## [2025.11.1] - 2025-11-07

### Added
- New feature X
- New feature Y

### Fixed
- Bug fix A
- Bug fix B

### Changed
- Change C
```

**Format Guidelines**:
- Use `## [VERSION] - YYYY-MM-DD` for the version header
- Group changes under `### Added`, `### Fixed`, `### Changed`, `### Removed`, `### Security`
- Use bullet points (`-`) for each change
- Be descriptive but concise

### 3. Commit the Changes

```bash
git add custom_components/unraid_management_agent/manifest.json CHANGELOG.md
git commit -m "Bump version to 2025.11.1"
git push origin main
```

### 4. Create and Push the Tag

```bash
# Create the tag
git tag v2025.11.1

# Push the tag to GitHub
git push origin v2025.11.1
```

**Alternative**: Create the tag directly on GitHub:
1. Go to **Releases** → **Draft a new release**
2. Click **Choose a tag** → Type `v2025.11.1` → **Create new tag**
3. Click **Publish release** (the workflow will run automatically)

### 5. Monitor the Workflow

1. Go to **Actions** tab in GitHub
2. Watch the **Release** workflow run
3. Verify all steps complete successfully
4. Check the release was created under **Releases**

### 6. Verify the Release

After the workflow completes:

1. **Check the Release Page**:
   - Go to **Releases** in GitHub
   - Verify the new release is listed
   - Check the release notes are correct
   - Verify the package file is attached

2. **Verify Package Contents**:
   - Download the `.zip` file
   - Extract and verify it contains the `unraid_management_agent` directory
   - Check that `manifest.json` has the correct version

3. **Test HACS Installation** (if applicable):
   - Add the repository to HACS
   - Verify the new version appears
   - Test installation

## Workflow Details

### Workflow File

Location: `.github/workflows/release.yml`

### Trigger

The workflow triggers on:
```yaml
on:
  push:
    tags:
      - 'v*'
```

Any tag starting with `v` will trigger the release workflow.

### Steps

1. **Checkout code**: Fetches the repository with full history
2. **Extract version**: Parses the tag to get the version number
3. **Verify version**: Ensures `manifest.json` version matches the tag
4. **Build package**: Creates a ZIP file of the integration
5. **Calculate checksum**: Generates SHA256 checksum for verification
6. **Extract release notes**: Pulls release notes from `CHANGELOG.md`
7. **Create release**: Creates the GitHub release with all assets
8. **Release summary**: Provides a summary in the workflow run

### Package Structure

The release package (`unraid_management_agent-VERSION.zip`) contains:

```
unraid_management_agent/
├── __init__.py
├── api_client.py
├── binary_sensor.py
├── button.py
├── config_flow.py
├── const.py
├── manifest.json
├── repairs.py
├── sensor.py
├── services.yaml
├── strings.json
├── switch.py
├── websocket_client.py
└── translations/
    └── en.json
```

**Excluded**:
- `*.pyc` files
- `__pycache__` directories
- `.git*` files
- `.DS_Store` files

## HACS Compatibility

The release workflow is designed to be fully compatible with HACS (Home Assistant Community Store):

### Requirements

1. ✅ **Repository Structure**: Integration in `custom_components/` directory
2. ✅ **manifest.json**: Valid manifest with all required fields
3. ✅ **Version Tags**: Semantic versioning with `v` prefix (e.g., `v2025.11.1`)
4. ✅ **Release Assets**: ZIP file attached to GitHub release
5. ✅ **hacs.json**: HACS metadata file (if needed)

### HACS Installation

Users can install via HACS:

1. **Add Custom Repository**:
   - HACS → Integrations → ⋮ → Custom repositories
   - Repository: `https://github.com/ruaan-deysel/ha-unraid-management-agent`
   - Category: Integration

2. **Install**:
   - Search for "Unraid Management Agent"
   - Click Download
   - Restart Home Assistant

3. **Configure**:
   - Settings → Devices & Services → Add Integration
   - Search for "Unraid Management Agent"
   - Follow the configuration flow

## Troubleshooting

### Version Mismatch Error

**Error**: `manifest.json version does not match tag`

**Solution**:
1. Check `manifest.json` has the correct version (without `v` prefix)
2. Ensure the tag matches (with `v` prefix)
3. Delete the tag if needed: `git tag -d v2025.11.1 && git push origin :refs/tags/v2025.11.1`
4. Fix the version and recreate the tag

### Package Not Created

**Error**: `Package file not found`

**Solution**:
1. Check the workflow logs for build errors
2. Verify the `custom_components/unraid_management_agent/` directory exists
3. Ensure all required files are present

### Release Notes Not Extracted

**Warning**: `No release notes found for version X in CHANGELOG.md`

**Solution**:
1. Check `CHANGELOG.md` has a section for the version: `## [2025.11.1]`
2. Ensure the format matches exactly (including brackets)
3. Verify there's content between the version header and the next version

### Workflow Permission Error

**Error**: `Resource not accessible by integration`

**Solution**:
1. Go to **Settings** → **Actions** → **General**
2. Under **Workflow permissions**, select **Read and write permissions**
3. Click **Save**
4. Re-run the workflow

## Best Practices

1. **Always update CHANGELOG.md** before creating a release
2. **Test locally** before pushing the tag
3. **Use semantic versioning** consistently
4. **Write clear release notes** that help users understand changes
5. **Verify the release** after the workflow completes
6. **Announce the release** in relevant channels (if applicable)

## Manual Release (Fallback)

If the automated workflow fails, you can create a release manually:

1. **Build the package**:
   ```bash
   cd custom_components
   zip -r ../unraid_management_agent-2025.11.1.zip unraid_management_agent/ \
     -x "*.pyc" -x "*__pycache__*" -x "*.git*" -x "*.DS_Store"
   ```

2. **Calculate checksum**:
   ```bash
   sha256sum unraid_management_agent-2025.11.1.zip > SHA256SUM
   ```

3. **Create release on GitHub**:
   - Go to **Releases** → **Draft a new release**
   - Choose the tag `v2025.11.1`
   - Add release notes from `CHANGELOG.md`
   - Attach the ZIP file and SHA256SUM file
   - Click **Publish release**

## Questions?

If you have questions about the release process:

1. Check this documentation
2. Review the workflow file: `.github/workflows/release.yml`
3. Look at previous releases for examples
4. Open an issue on GitHub

---

**Last Updated**: 2025-11-07

