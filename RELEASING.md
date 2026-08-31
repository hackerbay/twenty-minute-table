# Releasing

How to change the book and publish the result.

There are two audiences for a release. The **website** updates itself the moment a release
lands. The **Amazon editions** do not — a release builds and attaches the files, but somebody
still has to upload them to KDP. That step is deliberately manual; see [Publishing to
Amazon](#publishing-to-amazon).

---

## One-time setup

Two things are missing until somebody with admin on the repo does them.

**1. Let the release workflow deploy: `FIREBASE_SERVICE_ACCOUNT`.**

The workflow deploys to Firebase from a GitHub runner, which cannot use your personal login. It
needs a *service account* — a robot Google account whose private key lives in the repository
secrets. Creating it is the one step here that mints a credential, which is why it is not
automated.

The workflow accepts either `FIREBASE_SERVICE_ACCOUNT_TWENTY_MINUTE_TABLE` (what the Firebase
CLI creates) or `FIREBASE_SERVICE_ACCOUNT` (what you would call a hand-made one), so use
whichever route you prefer.

*Route A — let the Firebase CLI do it (recommended).*

**Run it from the directory that contains `firebase.json`**, which is the repository root. Get
that wrong and the CLI walks you through picking a project and then stops with
`Didn't find a Hosting config in firebase.json` — it is describing the directory you are
standing in, not a problem with the repo. On a machine where the working copy sits inside
another folder, that is an easy mistake to make:

```bash
cd "$(git rev-parse --show-toplevel)"   # the repo root, wherever you cloned it
ls firebase.json                        # this must exist before going further

firebase login                          # if you are not already
firebase init hosting:github
```

It will:

1. Ask for the repository — answer `hackerbay/twenty-minute-table`.
2. Open a browser to authorise the Firebase CLI's GitHub app. Approve it.
3. Create the service account, grant it Firebase Hosting rights, and store its key as the
   repository secret `FIREBASE_SERVICE_ACCOUNT_TWENTY_MINUTE_TABLE`.
4. Offer to set up a build script and automatic deployment on merge to `main`. **Decline the
   automatic deployment**, or delete the `firebase-hosting-*.yml` files it writes — this repo
   deploys from the `release` branch, and leaving those in place would publish every commit to
   `main` as well.

*Route B — by hand, through the Google Cloud console.*

1. Open the [service accounts page](https://console.cloud.google.com/iam-admin/serviceaccounts?project=twenty-minute-table)
   for the `twenty-minute-table` project.
2. **Create service account.** Name it something like `github-actions-deploy`.
3. Grant it the **Firebase Hosting Admin** role. (Add **Firebase Authentication Admin** too if
   you want preview channels to stop warning about auth domains.)
4. Open the account, go to **Keys → Add key → Create new key → JSON**, and download it.
5. In GitHub: **Settings → Secrets and variables → Actions → New repository secret.** Name it
   `FIREBASE_SERVICE_ACCOUNT` and paste the **entire contents** of the JSON file as the value —
   the whole `{ ... }`, not a path to it.
6. **Delete the downloaded JSON.** It is a live credential; it must never be committed, and
   there is no reason to keep a copy once GitHub has it.

*Check it worked* — this lists names only, never values:

```bash
gh secret list --repo hackerbay/twenty-minute-table
```

If the deploy step later fails with a permissions error, the service account is missing the
Hosting Admin role; if it fails parsing, the secret probably holds a file path or a partial
paste rather than the whole JSON.

**2. Create the `release` branch.** Everything on `main` is a candidate; `release` is what has
actually shipped.

```bash
git switch -c release main
git push -u origin release
```

Pushing that branch fires the release workflow immediately, so do it only when `main` is in a
state you are happy to publish.

---

## Making a change

`recipes/` is the source of truth. Everything else — the book, the covers, the Kindle edition,
the website, every page number and every statistic — is generated from it.

```bash
npm install                # once
python3 book/site.py       # fast loop: rebuilds the website, skips the PDF render
```

Use that while you are iterating. It takes seconds. The full build takes several minutes
because it paginates and vertically justifies 224 pages in a headless browser.

When you are done:

```bash
make verify                # structure: the recipe file contract
make audit                 # content: conversions, unused ingredients, doneness, repetition
make                       # verify, audit, the book, the website
```

Both gates must come back clean — `No problems found` and `0 findings`. They are strict on
purpose: they are what keeps a hundred recipes consistent enough to typeset automatically.
[AGENTS.md](AGENTS.md) documents the contract they enforce and the house style rules that will
fail your build (no exclamation marks, no cookbook filler, metric first).

If you touched the print geometry, the art, or anything under `book/`, build the Amazon
artefacts too and look at them:

```bash
make amazon                # interior, covers, Kindle edition, with their own gates
```

**Commit the regenerated output.** `dist/` and `site/` are committed, and CI fails a pull
request whose `site/` does not match what its `recipes/` generate. That check is the thing that
stops a recipe landing without its rebuilt pages.

---

## Choosing a version

`package.json` holds the version and nothing else does. `book/version.py` reads it, and it
surfaces on the book's cover, in the colophon, and in the website footer. Never write a version
anywhere else.

Read semantic versioning the way a cookbook needs it:

| Bump | For |
|---|---|
| **Patch** — `1.0.1` | A correction. A wrong conversion, an optimistic timing, a typo, a dead link. |
| **Minor** — `1.1.0` | New recipes, a new section, a new feature on the website. |
| **Major** — `2.0.0` | Anything that reorganises the book: renumbering recipes, changing the recipe file contract, dropping a section. |

A version is published once and never moved. People download the PDF; a tag that shifts under
them is worse than a second release.

---

## Cutting the release

```bash
# 1. bump the version
$EDITOR package.json                     # "version": "1.1.0"

# 2. write down what changed
$EDITOR CHANGELOG.md                     # move Unreleased items under the new heading

# 3. rebuild everything the version appears on, and look at it
make amazon
open dist/The-20-Minute-Table.pdf        # the cover foot and colophon should read v1.1.0

# 4. commit the sources and the regenerated output together
git add -A
git commit -m "Release 1.1.0"
git push origin main

# 5. wait for CI on main to pass, then ship it
git switch release
git merge --ff-only main
git push origin release
```

The `--ff-only` matters: `release` should only ever move forward to a commit that already
passed CI on `main`.

### What happens then

The release workflow, on any push to `release`:

1. Reads the version from `package.json` and derives the tag `v<version>`.
2. **Refuses to run if that tag already exists.** Bump the version; do not try to move a tag.
3. Runs `make verify` and `make audit`.
4. Builds the interior, the covers, the Kindle edition and the website in a single pass.
5. Deploys the website to Firebase Hosting, live.
6. Tags the commit and pushes the tag.
7. Publishes a GitHub release with notes generated from the commits since the previous tag,
   with four files attached: the print PDF, the Kindle EPUB, the paperback cover wrap, and the
   Kindle cover.

You can also run it by hand from the Actions tab — it accepts `workflow_dispatch`.

### After it finishes

```bash
curl -sSI https://twentyminutetable.hackerbay.io/ | head -1        # expect HTTP/2 200
curl -s   https://twentyminutetable.hackerbay.io/ | grep -o 'v[0-9.]*</span>'
gh release view "v1.1.0" --repo hackerbay/twenty-minute-table
```

The site is served with `no-cache` on HTML, so a hard refresh is not needed — the new version
should show immediately.

---

## When something goes wrong

**The workflow failed before deploying.** Nothing shipped. Fix it on `main`, then fast-forward
`release` again. No tag was created, so the version is still free.

**The workflow deployed but a later step failed.** The site is live and correct; only the tag or
the GitHub release is missing. Re-run the job from the Actions tab.

**A bad release went live.** Roll the site forward, never backward — fix the problem on `main`,
bump the patch version, and release again. Deleting a tag that people may already have pulled
causes more confusion than a fast follow-up.

**A release refused to run because the tag exists.** That is the guard working. You pushed to
`release` without bumping `package.json`. Bump it.

---

## Publishing to Amazon

A release does not touch Amazon. It builds and attaches the files; uploading them to KDP is a
human step, on purpose — pricing, categories and proofs are decisions, not automation.

Take the four files from the GitHub release:

| File | Where it goes |
|---|---|
| `The-20-Minute-Table-vX.Y.Z.pdf` | interior for **both** the paperback and the hardback |
| `cover-paperback-vX.Y.Z.pdf` | the paperback cover wrap |
| `The-20-Minute-Table-vX.Y.Z.epub` | the Kindle edition |
| `cover-kindle-vX.Y.Z.jpg` | the Kindle cover |

### Pricing and margin

```bash
make pricing
```

Amazon pays 60% of list minus the printing cost on a print book, and 70% minus a per-megabyte
delivery fee on Kindle. On a 224-page colour book the printing cost dominates everything, so
`pricing.py` computes the lowest list price each edition needs to clear its target margin
(25%, set in `imprint.py`) and fails if a configured price does not. It runs as part of
`make amazon`, so you cannot prepare a submission whose economics do not work. CI does not run
it — a business decision nobody has made yet should not turn the build red.

Two things it will tell you that are worth knowing before you price anything:

- **Premium colour is the whole problem.** At 224 pages it costs about $18.92 a copy, so 25%
  margin needs a list price around **$54**. Standard colour costs about $6.71 and clears the
  same margin at about **$19**. Every 10 pages you cut takes roughly $2.29 off the minimum
  price. That is the trade; the build states it rather than assuming an answer.
- **Kindle is comfortable.** At 4.2 MB the delivery fee is about $0.63, so $9.99 returns about
  64% — well clear of the target, and the figure is conservative because Amazon charges on the
  converted file, which is smaller than the EPUB.

Every number behind this is marked UNVERIFIED in `imprint.py`. Put the real figures from KDP's
printing-cost calculator in `INK` and `HARDBACK_PRINT_COST_USD` before trusting any of it.

Before the first submission:

- **Register the ISBNs at Bowker.** They are allocated in [book/imprint.py](book/imprint.py)
  from HackerBay's own block — `978-1-950600-01-4` for the paperback, `978-1-950600-02-1` for
  the hardback — so the publisher of record is yours rather than Amazon's. They are reserved,
  not registered: assigning them against the title at
  [myidentifiers.com](https://www.myidentifiers.com/isbn_dashboard) means entering real
  publication metadata, so it is a deliberate step. The Kindle edition uses an ASIN and needs
  no ISBN.
- Generate the **hardback case** from KDP's cover calculator. `make covers` prints the trim,
  page count and paper to feed it. KDP publishes no hardcover formula, so the build will not
  invent one.
- Confirm the numbers flagged as unverified at the end of
  [docs/kdp-publishing-spec.md](docs/kdp-publishing-spec.md) — in particular the printing cost,
  which decides whether the economics work at all.
- Run the EPUB through Adobe epubcheck and Kindle Previewer 3. `make epub` runs a structural
  check with no Java dependency, but it is not a substitute for those.
- **Order a physical proof of both print editions** and check the gutter, the bleed and the
  folio with a ruler. It is the only way to settle the margin question the spec flags.

Note that the free PDF on the website makes the Kindle edition ineligible for KDP Select. The
70% royalty in the US, UK and EU does not depend on Select; what you give up is Kindle Unlimited.

---

## Quick reference

| Command | What it does |
|---|---|
| `python3 book/site.py` | website only, seconds, no PDF render |
| `make verify` | the recipe file contract |
| `make audit` | conversions, unused ingredients, doneness, repeated prose |
| `make` | verify, audit, book, website |
| `make amazon` | verify, audit, interior, covers, Kindle edition, margin check |
| `make pricing` | minimum list price per edition for the target margin |
| `make kdp` | re-check the built interior against KDP's requirements |
| `make clean` | remove `build/` and `site/` |
