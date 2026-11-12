# ripgrep (`rg`) - Fast Search Commands

Use ripgrep (`rg`) for fast, gitignore-aware code and text search. Prefer `rg` over `grep`, `find`, or recursive shell loops when searching a repository.

## Key Commands

```bash
# Search text
rg "pattern"                         # search current directory
rg "pattern" path/to/dir             # search within a directory
rg -n "pattern"                      # show line numbers (default in many outputs)
rg -i "pattern"                      # case-insensitive search
rg -S "pattern"                      # smart case search
rg -w "word"                         # match whole word
rg -F "literal.text"                 # fixed-string search, not regex

# Search files
rg --files                            # list files respected by ignore rules
rg --files -g "*.ts"                 # list matching files
rg --files -g '!dist/**'              # exclude paths with glob
rg --files --hidden                   # include hidden files, still respects ignore files
rg --files --no-ignore                # ignore .gitignore/.ignore rules

# Filter by file type or glob
rg "pattern" -t ts                    # only TypeScript files
rg "pattern" -t py                    # only Python files
rg "pattern" -T test                  # exclude recognized test files
rg "pattern" -g "*.md"               # include glob
rg "pattern" -g '!package-lock.json'  # exclude glob

# Context and output shaping
rg -C 2 "pattern"                     # 2 lines before and after
rg -A 3 "pattern"                     # 3 lines after
rg -B 3 "pattern"                     # 3 lines before
rg -l "pattern"                       # files with matches only
rg -L "pattern"                       # files without matches
rg --count "pattern"                  # match count per file
rg --json "pattern"                   # machine-readable output

# Regex examples
rg "TODO|FIXME"                       # alternation
rg "function\s+\w+"                  # regex search
rg "class\s+\w+" -t py               # regex in Python files

# Replacement preview / rewrite helper
rg "oldName" -n                       # preview matches before editing
rg "oldName" -l                       # files to update with editor or script
```

## Rules

- Prefer `rg "pattern"` for repository search.
- Use `rg --files` instead of recursive `find` when listing project files.
- Use `-F` for literal strings that contain regex characters.
- Use `-g` globs to include/exclude paths instead of piping through extra shell commands.
- Use `--hidden` only when dotfiles are relevant.
- Use `--no-ignore` only when ignored files are explicitly needed.
- For very broad searches, scope by path, file type, or glob to reduce noise.
- For scripted parsing, prefer `--json` over brittle text parsing.
