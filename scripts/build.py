#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; STORIES=ROOT/'stories'; SITE=ROOT/'site'
def load(p):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception as e:raise ValueError(f'{p.relative_to(ROOT)}: invalid JSON: {e}')
def build_reader(story,scenes):
 slug=story['slug']; target=SITE/'stories'/slug;target.mkdir(parents=True,exist_ok=True)
 payload=json.dumps({'story':story,'scenes':scenes['scenes']},ensure_ascii=False).replace('</','<\\/')
 page="""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>Katha Loka Reader</title><link rel="stylesheet" href="/assets/css/site.css"><link rel="stylesheet" href="/assets/css/reader.css"><script defer src="/assets/js/reader.js"></script><script defer src="/assets/js/story-actions.js"></script></head><body><header class="reader-top"><a href="/">✿ Katha Loka · ಕಥಾಲೋಕ</a><div><a href="/" id="home-link">← Story library</a> <select id="reader-language"><option value="en">English</option><option value="kn">ಕನ್ನಡ</option></select></div></header><main class="reader-main"><div id="reader-content"></div><nav class="reader-nav"><button id="previous-scene">← Previous</button><span id="scene-position"></span><button id="next-scene">Next →</button></nav></main><script id="story-payload" type="application/json">__PAYLOAD__</script></body></html>""".replace('__PAYLOAD__',payload)
 (target/'index.html').write_text(page,encoding='utf-8')
def main():
 published=[]
 for p in sorted(STORIES.glob('*/story.json')):
  s=load(p)
  for k in ('slug','status','title','description','cover','sceneCount'):
   if k not in s:raise ValueError(f'{p}: missing {k}')
  if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',s['slug']):raise ValueError(f'{p}: invalid slug')
  for field in ('title','description'):
   for l in ('en','kn'):
    if not s[field].get(l):raise ValueError(f'{p}: {field}.{l} required')
  if s['status']!='published':continue
  sp=p.parent/'scenes.json'; scenes=load(sp)
  if len(scenes.get('scenes',[]))!=s['sceneCount']:raise ValueError(f'{sp}: sceneCount mismatch')
  for i,scene in enumerate(scenes['scenes'],1):
   for l in ('en','kn'):
    if not scene.get('narration',{}).get(l):raise ValueError(f'{sp}: scene {i} narration.{l} required')
   for line in scene.get('dialogue',[]):
    for l in ('en','kn'):
     if not line.get(l):raise ValueError(f'{sp}: dialogue in scene {i} missing {l}')
  published.append(s);build_reader(s,scenes)
 (SITE/'stories.json').write_text(json.dumps({'stories':published},ensure_ascii=False,indent=2),encoding='utf-8')
 print(f'Build complete: {len(published)} published stories -> {SITE}')
if __name__=='__main__':
 try:main()
 except (ValueError,OSError) as e:print('BUILD ERROR:',e,file=sys.stderr);sys.exit(1)
