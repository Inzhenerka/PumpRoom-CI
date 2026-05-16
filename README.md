# PumpRoom-CI

Shared, reusable GitHub Actions workflows for Inzhenerka / PumpRoom projects.

Call these from any consumer repo with `workflow_call` — no copy-pasting CI logic.

## Workflows

### `deploy_site.yml` — Static site → Yandex Cloud

Builds a Bun project, syncs the output to a Yandex Object Storage bucket, and purges the Yandex CDN cache via the Cloud API.

```yaml
jobs:
  deploy:
    uses: Inzhenerka/PumpRoom-CI/.github/workflows/deploy_site.yml@main
    with:
      environment: production
      url: https://example.com
      site_folder: dist
      s3_bucket: my-bucket
      cdn_resource_id: bc8xxxxxxxxxxxxxxxxx
    secrets:
      yc_sa_json_credentials: ${{ secrets.YC_SA_JSON_CREDENTIALS }}
      access_key_id:          ${{ secrets.AWS_ACCESS_KEY_ID }}
      secret_access_key:      ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

**Required secrets**

| Secret | Purpose |
|---|---|
| `yc_sa_json_credentials` | Yandex Cloud service-account JSON key (CDN purge) |
| `access_key_id` / `secret_access_key` | Static keys for the S3-compatible bucket |

### `deploy_coolify.yml` — Docker image → Coolify

Builds and pushes a multi-arch Docker image to a registry (defaults to GHCR), then triggers a Coolify deploy webhook.

```yaml
jobs:
  deploy:
    uses: Inzhenerka/PumpRoom-CI/.github/workflows/deploy_coolify.yml@main
    with:
      dockerfile: ./Dockerfile
      platforms: linux/amd64,linux/arm64
      environment: production
      url: https://app.example.com
    secrets:
      coolify_webhook: ${{ secrets.COOLIFY_WEBHOOK }}
      coolify_token:   ${{ secrets.COOLIFY_TOKEN }}
      build_args:      ${{ secrets.BUILD_ARGS }}  # optional, KEY=VALUE per line
```

Image is tagged with the branch name, short SHA, and `latest` on the default branch. Build cache uses GitHub Actions cache (`type=gha`).

**Required secrets**

| Secret | Purpose |
|---|---|
| `coolify_webhook` | Coolify deploy webhook URL |
| `coolify_token` | Coolify API bearer token |
| `build_args` | (optional) Multiline `KEY=VALUE` build args, masked in logs |

## Versioning

Pin to a tag (`@v1`, `@v1.2.0`) once releases are cut. Until then, pin to a commit SHA for reproducibility; `@main` tracks the latest.
