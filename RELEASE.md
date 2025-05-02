# Release Process

## Automated Release Process

1. Bump the version using the script:
   ```
   python scripts/bump_version.py [major|minor|patch]
   ```

2. Commit the changed setup.py file:
   ```
   git add setup.py
   git commit -m "Bump version to x.y.z"
   ```

3. Push the changes:
   ```
   git push origin main
   ```

4. Create a new release on GitHub:
   - Go to the repository on GitHub
   - Click on "Releases"
   - Click "Create a new release"
   - Enter a tag (e.g., v0.9.2)
   - Enter a release title (e.g., "Version 0.9.2")
   - Add release notes (what's new, bug fixes, etc.)
   - Click "Publish release"

5. The GitHub Actions workflow will automatically:
   - Build the package
   - Upload it to PyPI

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