# Removed pre-commit setup

Pre-commit hook configuration was removed from the repository.

If you want to restore it later:

1. Recreate `.pre-commit-config.yaml` (see prior commit history for reference).
2. Add `.flake8` and `.prettierrc.json` as needed.
3. Add dependencies back to `requirements.txt`:
   - black
   - flake8
   - pre-commit
4. Run:
   ```bash
   pre-commit install
   pre-commit run --all-files
   ```

This placeholder file exists to document the intentional removal so that future contributors understand why the config is missing.
