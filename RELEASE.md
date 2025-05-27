# Release Process

## Version Numbering Guidelines

Our project follows Semantic Versioning (SemVer) with version numbers formatted as `MAJOR.MINOR.PATCH`. When deciding which version component to bump, use these guidelines:

## Fully Automated Release Process

1. Bump the version using the script:
 ```
 python scripts/bump_version.py [major|minor|patch]
 ```
2. Commit with a message containing "Bump version":
 ```
 git add tools/version.py
 git commit -m "Bump version to x.y.z"
 ```
3. Push directly to main or create and merge a PR to main:
 ```
 git push origin main
 ```
4. The GitHub Actions workflow will automatically:
- Detect the version bump commit
- Create a new release with the version from tools/version.py
- Generate release notes
- Build the package
- Upload it to PyPI

No manual intervention is required after pushing the version bump commit!

### Patch Version (x.y.Z)

Bump the patch version (e.g., 0.9.12 → 0.9.13) when making **backward-compatible bug fixes**:

- Bug fixes that don't change the API
- Performance improvements with no API changes
- Small code optimizations
- Typo corrections
- Documentation updates
- Internal code reorganization with no user impact

**Examples:**
- Fixing a calculation error
- Correcting a race condition
- Improving error messages
- Optimizing an algorithm without changing its behavior

### Minor Version (x.Y.z)

Bump the minor version (e.g., 0.9.12 → 0.10.0) when adding **backward-compatible functionality**:

- New features that don't break existing code
- New optional parameters to functions/methods
- New functions/methods/classes
- Deprecation notices (but still keeping backward compatibility)
- New configuration options

**Examples:**
- Adding a new tool to galago-tools
- Adding a new parameter with a default value
- Adding a new method to a class
- Supporting a new file format

### Major Version (X.y.z)

Bump the major version (e.g., 0.9.12 → 1.0.0) when making **incompatible API changes**:

- Breaking changes that require users to modify their code
- Removing deprecated features
- Changing function/method signatures
- Renamed functions or classes
- Changed behavioral semantics of existing functions
- Modifications to return values or exceptions thrown

**Examples:**
- Renaming a critical function
- Removing support for an old protocol
- Changing the meaning of a parameter
- Restructuring the entire API

### Special Case: Initial Development (0.x.y)

When the major version is 0 (e.g., 0.9.12), the project is considered to be in "initial development" phase:
- API is not considered stable
- Changes might be more frequent
- Minor version bumps might include breaking changes

Moving to 1.0.0 signifies that the API is considered stable and ready for production use.



## Setting Up Credentials

Before you can use the automated release process, you need to set up a PyPI API token:

1. Create a PyPI API token:
- Go to [https://pypi.org/manage/account/](https://pypi.org/manage/account/)
- Go to API tokens
- Create a new token with scope "Upload to PyPI"
- Copy the token

2. Add the token to GitHub Secrets:
- Go to your repository on GitHub
- Go to "Settings" > "Secrets and variables" > "Actions" 
- Click "New repository secret"
- Name: `PYPI_API_TOKEN`
- Value: Paste your PyPI API token
- Click "Add secret"

## Manual Release Process (if needed)

If you need to release manually:

1. Bump the version in tools/version.py
2. Build the package:
 ```
 python -m build
 ```
3. Upload to PyPI:
 ```
 python -m twine upload dist/galago_tools-x.y.z*
 ```

When prompted, enter your PyPI API token as the password.
