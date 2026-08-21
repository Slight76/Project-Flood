# Install, Migrate, Upgrade, and Uninstall

Project Flood v0.2 records baseline hashes in `.project-flood/install-manifest.yaml`.

## Commands

```bash
python scripts/flood.py diff --target /path/to/repo
python scripts/flood.py install --target /path/to/repo --mode full
python scripts/flood.py upgrade --target /path/to/repo
python scripts/flood.py migrate --target /path/to/v0.1/repo
python scripts/flood.py migrate --target /path/to/v0.1/repo --apply
python /path/to/repo/.project-flood/flood.py doctor --root /path/to/repo
python /path/to/repo/.project-flood/flood.py uninstall --root /path/to/repo
python /path/to/repo/.project-flood/flood.py uninstall --root /path/to/repo --yes
```

Task-lease commands are intentionally separate from installation lifecycle commands; an upgrade never activates, overwrites, or closes a worktree lease.

`diff`, `migrate`, and `uninstall` are dry runs by default. Installation refuses conflicting customized files unless `--force` is given. Forced replacements, v0.1 removals, and uninstall operations are backed up under the gitignored `.project-flood/backups/` directory.

During upgrade:

- unchanged managed files may update safely;
- target-only customizations are preserved;
- a file changed by both Project Flood and the target is a conflict;
- framework files removed in a release are removed only when still unchanged;
- customized removed files become unmanaged and remain in place.

The v0.1 migrator explicitly removes the old unnamespaced agents, prompts, and skills after backing them up; otherwise they would collide with v0.2 discovery.
