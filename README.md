# Katha Loka Story Engine

Responsive, bilingual (English/Kannada) static story library and reader for Cloudflare Pages. Each story is source data under `stories/<slug>/`; a Python build validates bilingual text and generates a static reader page plus `site/stories.json`. No paid API is required.

## Local build
```bash
python3 scripts/build.py
python3 -m http.server 8788 --directory site
```
Open http://127.0.0.1:8788.

## Add a story
```bash
python3 scripts/new_story.py the-lion-and-the-mouse
```
Edit `stories/the-lion-and-the-mouse/story.json` and `scenes.json`, add a cover to `site/assets/images/` and scene images into that story folder. Each scene needs narration in both `en` and `kn`; dialogue needs both translations. Match `sceneCount`, review art and Kannada, then set `status` to `published`. Build:
```bash
python3 scripts/build.py
```
The engine wires the text and images into the site. It does not auto-create original illustrations or guarantee translation quality; provide/commission art you have rights to use and review Kannada with a fluent speaker.

## Git
If new repository:
```bash
git init
git add .
git commit -m "Initial Katha Loka story engine"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main
```
If already a repo, use `git status`, then `git add .`, `git commit -m "Build bilingual story engine"`, `git push`.

## Cloudflare Pages
Push to GitHub, then Cloudflare Dashboard → Workers & Pages → Create → Pages → Connect to Git. Set build command `python3 scripts/build.py`, output directory `site`. Deploy. If Cloudflare's build image lacks Python, run the build in GitHub Actions and deploy the `site` artifact using Cloudflare's supported Pages action; keep account IDs/tokens in repository secrets, never commit them.

## Publishing workflow
1. Give the engine a story idea or write bilingual story source.
2. Run `python3 scripts/new_story.py slug-name`.
3. Add/edit the bilingual story metadata and scenes; add licensed/original cover and scene images.
4. Run `python3 scripts/build.py`; fix validation errors.
5. Preview locally, check desktop and mobile, proofread both languages.
6. `git add stories site && git commit -m "Add story: title" && git push`.
7. Cloudflare Pages redeploys the site from Git.

The app is reader-first. It has no story-creation controls for children. The story-source files and build scripts are for the site owner/developer.
