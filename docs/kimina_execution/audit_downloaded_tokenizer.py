"""Compare downloaded receipts with a locally downloaded, pinned tokenizer."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, '/Users/friedrichreichelt/Documents/verified-reasoning-monitoring/src')
from transformers import AutoTokenizer
from vrm.runtime import encode_prompt

directory = Path('/private/tmp/kimina-tokenizer-audit')
roots = [Path('/Users/friedrichreichelt/Downloads/results'), Path('/Users/friedrichreichelt/Downloads/results 2')]
paths = {p.name: p for root in roots for p in root.glob('*.json')}
request = json.loads(paths['request.json'].read_text())
tokenizer = AutoTokenizer.from_pretrained(directory, local_files_only=True)
generation = json.loads((directory / 'generation_config.json').read_text())
rows = []
for attempt in request['attempts']:
    key = f"{attempt['task_id']}-{attempt['index']:03d}"
    candidate = json.loads(paths[key + '.json'].read_text())['payload']['candidate']
    ids = encode_prompt(tokenizer, attempt['messages'], 16384)
    rendered = tokenizer.apply_chat_template(attempt['messages'], tokenize=False, add_generation_prompt=True)
    assert ids == tokenizer(rendered, add_special_tokens=False)['input_ids']
    assert ids == candidate['input_ids'], key
    assert tokenizer.decode(candidate['output_ids'], skip_special_tokens=True) == candidate['text'], key
    assert rendered.endswith('<|im_start|>assistant\n')
    assert tokenizer.bos_token_id is None
    assert ids[0] == tokenizer.convert_tokens_to_ids('<|im_start|>')
    eos = generation['eos_token_id']
    rows.append(dict(key=key, input_ids_match=True, raw_decoding_matches=True,
                     input_tokens=len(ids), last_output_token=candidate['output_ids'][-1],
                     terminal_eos=candidate['output_ids'][-1] in eos))
report = dict(model_revision='1dfd2228afcc35b16eb008a81dfc2b2707750f78',
              tokenizer_file_hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in directory.glob('*.json')},
              bos_token_id=tokenizer.bos_token_id, eos_token_id=tokenizer.eos_token_id,
              pad_token_id=tokenizer.pad_token_id, official_generation_config=generation,
              rows=rows, scope='Real tokenizer and saved token IDs, no model inference')
Path('/private/tmp/kimina-tokenizer-audit-result.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
