# Version

Current package version:

```text
0.1.0
```

The version is defined in `pyproject.toml`.

```toml
[project]
name = "kernelbox"
version = "0.1.0"
```

## Versioned docs

The docs are ready for versioned publishing with `mike`.

Build local docs:

```powershell
uv run zensical build
```

Serve local docs:

```powershell
uv run zensical serve
```

Publish a version with mike:

```powershell
uv run mike deploy --push --update-aliases 0.1.0 latest
```

Set the default docs version:

```powershell
uv run mike set-default --push latest
```

