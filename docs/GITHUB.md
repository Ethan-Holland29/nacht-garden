# Push this folder to GitHub

This directory is an independent Git repository on the `main` branch. No remote or public repository is configured. It contains source, documentation and numeric evidence only.

From this folder:

```bash
python3 tools/check_repo.py
git status --short
git add .
git commit -m "Add Nacht Garden proof of concept"
```

Create an empty GitHub repository with your preferred name and visibility. Then use its URL:

```bash
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

Use your own Git name/email if Git asks for author configuration. The export does not select an identity, create a remote, publish code or choose a license for you.

The included GitHub Actions workflow repeats source/notebook checks on pushes and pull requests. It does not run the game or the cloud benchmark.

If running the notebook locally, clear its output before committing. Generated assets are ignored, and the source check also examines tracked files to catch accidentally force-added content. Review the actual staged diff before publishing.
