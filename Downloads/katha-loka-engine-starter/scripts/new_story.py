#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
if len(sys.argv)!=2: raise SystemExit('Usage: python3 scripts/new_story.py slug-name')
slug=sys.argv[1].lower()
if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug): raise SystemExit('Use lowercase words separated by hyphens.')
p=Path(__file__).resolve().parents[1]/'stories'/slug
if p.exists(): raise SystemExit(f'{p} already exists')
p.mkdir(parents=True)
story={'slug':slug,'status':'draft','ageLabel':'AGES 6–8','sceneCount':5,'cover':f'/assets/images/{slug}-cover.jpg','coverAlt':{'en':'Story cover','kn':'ಕಥೆಯ ಮುಖಪುಟ'},'category':{'en':'NEW STORY','kn':'ಹೊಸ ಕಥೆ'},'title':{'en':'Add English title','kn':'ಕನ್ನಡ ಶೀರ್ಷಿಕೆ ಸೇರಿಸಿ'},'description':{'en':'Add a short description.','kn':'ಚಿಕ್ಕ ವಿವರಣೆ ಸೇರಿಸಿ.'},'moral':{'en':'','kn':''}}
scenes={'slug':slug,'scenes':[{'id':f'scene-{i:02}','image':f'scene-{i:02}.jpg','narration':{'en':f'Add English narration for scene {i}.','kn':f'{i}ನೇ ದೃಶ್ಯದ ಕನ್ನಡ ನಿರೂಪಣೆ ಸೇರಿಸಿ.'},'dialogue':[]} for i in range(1,6)]}
(p/'story.json').write_text(json.dumps(story,ensure_ascii=False,indent=2),encoding='utf-8')
(p/'scenes.json').write_text(json.dumps(scenes,ensure_ascii=False,indent=2),encoding='utf-8')
print('Created',p,'— edit both JSON files, add art, then set status to published.')
