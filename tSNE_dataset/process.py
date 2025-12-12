import json
t = json.load(open('./tsne_output/gmner_tsne_multimodal_layer28.json'))
with open('./temp.txt', 'w') as f:
    f.write('\n'.join([f"{i['x']}\t{i['y']}" for i in t]))
