---
name: git-advanced-workflows
description: Advanced Git techniques for maintaining clean history, cherry-picking, bisect, worktrees, reflog recovery. Use when cleaning up commit history before merging, applying commits across branches, finding bug-introducing commits, working on multiple features simultaneously, or recovering from Git mistakes.
version: 1.0.0
author: soponcd
license: MIT-0
---

# Git Advanced Workflows

Master advanced Git techniques to maintain clean history, collaborate effectively, and recover from any situation with confidence.

## When to Use This Skill

- Cleaning up commit history before merging
- Applying specific commits across branches
- Finding commits that introduced bugs
- Working on multiple features simultaneously
- Recovering from Git mistakes or lost commits
- Managing complex branch workflows
- Preparing clean PRs for review
- Synchronizing diverged branches

## Core Concepts

### 1. Interactive Rebase

```bash
# Rebase last 5 commits
git rebase -i HEAD~5

# Rebase all commits on current branch
git rebase -i $(git merge-base HEAD main)
```

Operations: `pick`, `reword`, `edit`, `squash`, `fixup`, `drop`

### 2. Cherry-Picking

```bash
# Cherry-pick single commit
git cherry-pick abc123

# Cherry-pick range of commits
git cherry-pick abc123..def456

# Cherry-pick without committing
git cherry-pick -n abc123
```

### 3. Git Bisect (Find Bug Introduction)

```bash
git bisect start
git bisect bad          # Mark current as bad
git bisect good v1.0.0  # Mark known good commit
# Test each commit Git checks out, then mark good/bad
git bisect reset        # Done
```

### 4. Worktrees (Multiple Branches Simultaneously)

```bash
# Add worktree for urgent bugfix
git worktree add ../project-hotfix hotfix/critical-bug

# List existing worktrees
git worktree list

# Remove when done
git worktree remove ../project-hotfix
```

### 5. Reflog (Safety Net)

```bash
# View reflog
git reflog

# Recover lost commits
git reflog
git reset --hard def456   # or git branch recovered-branch abc123
```

## Practical Workflows

### Clean Up Feature Branch Before PR

```bash
git checkout feature/user-auth
git rebase -i main
# Squash WIP commits, reword messages, drop unnecessary commits
git push --force-with-lease origin feature/user-auth
```

### Apply Hotfix to Multiple Releases

```bash
# Create fix on main, then cherry-pick to releases
git checkout release/2.0 && git cherry-pick abc123
git checkout release/1.9 && git cherry-pick abc123
```

### Recover from Mistakes

```bash
git reflog                  # Find lost commit hash
git reset --hard def456     # Restore to that commit
# or
git branch recovery def456  # Create branch from lost commit
```

## Best Practices

1. **Always use `--force-with-lease`** instead of `--force`
2. **Rebase only local commits** — don't rebase commits already shared
3. **Create backup branch** before risky operations: `git branch backup-branch`
4. **Atomic commits** — each commit = one logical change
5. **Test after rebase** — ensure history rewrite didn't break anything
6. **Reflog lasts 90 days** — your safety net for mistakes

## Recovery Commands

```bash
# Abort operations in progress
git rebase --abort
git merge --abort
git cherry-pick --abort
git bisect reset

# Undo last commit but keep changes
git reset --soft HEAD^

# Undo last commit and discard changes
git reset --hard HEAD^

# Recover deleted branch (within 90 days)
git reflog
git branch recovered-branch abc123
```
