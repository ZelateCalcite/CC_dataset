import json
gmner_texts = []
gmner_images = []
for split in ['train', 'val', 'test']:
    with open(f'../data/gmner/{split}_raw.json') as f:
        data = json.load(f)
    for d in data:
        gmner_texts.append(' '.join(d['tokens']))
        gmner_images.append(d['id'])
    pass
with open(f'gmner.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps([{'text': gmner_texts[i], 'image_id': gmner_images[i]} for i in range(len(gmner_texts))]))

wmner_texts = []
wmner_images = []
for split in ['train', 'val', 'test']:
    with open(f'../data/wmner/{split}_raw.json', encoding='utf-8') as f:
        data = json.load(f)
    for d in data:
        wmner_texts.append(d['text'])
        wmner_images.append(d['id'])
    pass
with open(f'wmner.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps([{'text': wmner_texts[i], 'image_id': wmner_images[i]} for i in range(len(wmner_texts))]))
