# Website Deployment

This website is a static site and can be deployed directly from the `website/` folder.

## Local preview

```bash
cd website
python3 -m http.server 4173
```

Open `http://127.0.0.1:4173`.

## Cloudflare Pages deployment (current target)

Project `themocs` -> https://themocs.pages.dev

The project is git-connected and builds on push. **These two settings in the
Pages dashboard are required**, and a build with anything else produces an
empty deployment that 404s every route:

| Setting                | Value                     |
| ---------------------- | ------------------------- |
| Build command          | `bash scripts/build-cf.sh` |
| Build output directory | `.cf-dist`                |

Do not leave the build command empty with the output directory set to
`website`. That publishes the folder wholesale, which is how `package.json`,
`vite.config.js` and `src/*.jsx` ended up fetchable on the Netlify site.

For an out-of-band deploy from a workstation:

```bash
scripts/deploy-cloudflare.sh              # preview deployment
scripts/deploy-cloudflare.sh --production # production branch
```

`scripts/build-cf.sh` stages a clean copy of `website/` into `.cf-dist/`, and
both the git build and the direct upload publish that staged tree rather than
`website/` itself. Netlify published the folder
wholesale, which put `package.json`, `vite.config.js` and `src/*.jsx` on the
public site; staging drops build sources and tooling. It also aborts if any
asset exceeds Cloudflare's 25 MiB per-file limit, or if `404.html` is missing
from the staged root.

`website/_headers` carries the security headers (CSP, HSTS, X-Frame-Options,
nosniff, Referrer-Policy, Permissions-Policy, X-Robots-Tag) and the no-AI rules
on the watermarked image folders. It is the Cloudflare equivalent of the
`[[headers]]` blocks in `netlify.toml`.

There is deliberately **no** `_redirects` file. Cloudflare documents that
"Redirects are always followed, regardless of whether or not an asset matches
the incoming request", so porting the Netlify `/* -> /index.html 200` rewrite
would shadow every real asset. This is a multi-page static site, so Pages'
directory-index serving handles routing on its own.

Two behaviours differ from Netlify and are expected:

- Netlify's Pretty URLs rewrote `href="agenda/index.html"` to `/agenda/` at the
  edge. Cloudflare serves the markup as authored; Pages 308-redirects
  `/agenda/index.html` to `/agenda/`, so links work with one extra hop.
- Netlify returned its homepage at status 200 for unmatched paths, via the SPA
  rewrite. Cloudflare serves `website/404.html` with a real 404 instead. That
  file is load-bearing: Cloudflare documents that "if your project does not
  include a top-level `404.html` file, Pages assumes that you are deploying a
  single-page application", and falls back to serving `/` at 200. Deleting it
  silently reintroduces soft 404s. Pages also serves it at `/404` and
  308-redirects `/404.html` there.

DNS still points at Netlify. Register the custom domain in the Pages project
**before** repointing DNS -- pointing a CNAME at Pages for a hostname the
project does not yet claim serves a cert that does not match, and browsers show
the site as insecure.

## Netlify deployment (legacy, still live)

A root `netlify.toml` is included and publishes the `website/` directory directly.

- No Node build step is required.
- SPA fallback redirect is included for route handling.

## Registration links

The homepage includes:

- Eventbrite registration button
- Eventbrite embedded registration panel
- Agenda copy button


## Deploy test branch

To test a non-production deployment, configure your Netlify site to track branch `deploy-test`.
