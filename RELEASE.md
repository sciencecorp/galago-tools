# Release Process

## Fully Automated Release Process

1. Bump the version using the script:
   ```
   python scripts/bump_version.py [major|minor|patch]
   ```

2. Commit with a message containing "Bump version":
   ```
   git add setup.py
   git commit -m "Bump version to x.y.z"
   ```

3. Push directly to main or create and merge a PR to main:
   ```
   git push origin main
   ```

4. The GitHub Actions workflow will automatically:
   - Detect the version bump commit
   - Create a new release with the version from setup.py
   - Generate release notes
   - Build the package
   - Upload it to PyPI

No manual intervention is required after pushing the version bump commit!

## Older Release Processes

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

1. Bump the version in setup.py
2. Build the package:
   ```
   python -m build
   ```
3. Upload to PyPI:
   ```
   python -m twine upload dist/galago_tools-x.y.z*
   ```

When prompted, enter your PyPI API token as the password. 