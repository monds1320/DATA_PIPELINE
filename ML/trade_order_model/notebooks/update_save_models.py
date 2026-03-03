import json

notebook_path = 'ml_pipeline.ipynb'
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

updated = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'models = {' in source and 'best_model_name =' in source:
            additional_code = """
# Save all trained models
print('\\n💾 Saving all trained models...')
for name, model in trained_models.items():
    with open(f'../models/model_{name}.pkl', 'wb') as f:
        pickle.dump(model, f)
    print(f'✅ Saved {name} model')
"""
            # Split the additional code into lines and append them to the source list
            lines = [line + '\n' for line in additional_code.strip('\n').split('\n')]
            cell['source'].extend(lines)
            updated = True
            break

if updated:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print("Notebook updated successfully. All models will now be saved.")
else:
    print("Could not find the target cell to update.")
