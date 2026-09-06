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

### `deploy_timeweb_site.yml` — Static site → Timeweb Cloud

Builds a Bun project, synchronizes the output to Timeweb Cloud S3, fully purges
the CDN resource, waits for the deployed URL to respond successfully, and then
creates a successful GitHub deployment.

```yaml
jobs:
  deploy:
    uses: Inzhenerka/PumpRoom-CI/.github/workflows/deploy_timeweb_site.yml@main
    with:
      environment: production
      url: https://example.com
      site_folder: ./build
      s3_bucket: example-site
      cdn_resource_id: '123456'
      # During migration, verify the technical CDN domain before DNS cutover:
      # smoke_test_url: https://example.cdn.twcstorage.ru
      # smoke_test_path: /index.html
    secrets:
      access_key_id:       ${{ secrets.TIMEWEB_S3_ACCESS_KEY_ID }}
      secret_access_key:   ${{ secrets.TIMEWEB_S3_SECRET_ACCESS_KEY }}
      timeweb_cloud_token: ${{ secrets.TIMEWEB_CLOUD_TOKEN }}
```

**Required secrets**

| Secret | Purpose |
|---|---|
| `access_key_id` / `secret_access_key` | Timeweb S3 user restricted to the site's bucket |
| `timeweb_cloud_token` | Timeweb Cloud API token used only for CDN cache purge |

For the first upload, pass the technical CDN domain as `smoke_test_url` and
`/index.html` as `smoke_test_path`. After DNS and TLS are ready, remove those
overrides so the workflow verifies the public site root. The Timeweb infra
workflow exports the required bucket name, CDN resource ID, and technical
domain in `timeweb-cdn.outputs.json`.

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
