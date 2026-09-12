"""Pinned, batch-one HF inference; real forwards are distinct from unit tests."""

import hashlib
import importlib.metadata
import platform
import time
from collections.abc import Mapping
from numbers import Integral

import numpy as np
import torch


def runtime_identity():
    packages = {}
    for name in ("torch", "transformers", "accelerate", "numpy", "scikit-learn"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    cuda = torch.cuda.is_available()
    return dict(python=platform.python_version(), platform=platform.platform(),
                packages=packages, cuda=cuda,
                gpu=torch.cuda.get_device_name(0) if cuda else None)


def encode_prompt(tokenizer, prompt, limit=512):
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be nonempty")
    # Applying the chat template tokenizes the BOS already; do not tokenize again.
    encoded = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}], tokenize=True,
        add_generation_prompt=True,
    )
    ids = encoded.get("input_ids") if isinstance(encoded, Mapping) else encoded
    if (not isinstance(ids, list) or not ids
            or any(isinstance(token, bool) or not isinstance(token, Integral)
                   for token in ids)):
        raise ValueError("chat template did not return token IDs")
    ids = [int(token) for token in ids]
    if ids[0] != tokenizer.bos_token_id or ids.count(tokenizer.bos_token_id) != 1:
        raise ValueError("expected exactly one initial BOS")
    if len(ids) > limit:
        raise ValueError(f"prompt exceeds token limit: {len(ids)} > {limit}")
    return ids


def capture_states(model, layers, ids, positions, *, device):
    if not positions or min(positions) < 0 or max(positions) >= len(ids):
        raise ValueError("capture positions outside input")
    saved, handles = {}, []
    def hook_for(index):
        def hook(_module, _inputs, output):
            hidden = output[0] if isinstance(output, tuple) else output
            if hidden.ndim != 3 or hidden.shape[0] != 1:
                raise ValueError("expected batch-one post-block residual stream")
            saved[index] = hidden[0, positions, :].detach().to("cpu", torch.float16)
        return hook
    try:
        for index, layer in enumerate(layers):
            handles.append(layer.register_forward_hook(hook_for(index)))
        with torch.inference_mode():
            model(input_ids=torch.tensor([ids], device=device), use_cache=False)
        if len(saved) != len(layers):
            raise ValueError("not every registered layer was captured")
        result = torch.stack([saved[i] for i in range(len(layers))], dim=1).numpy()
        if not np.isfinite(result).all():
            raise ValueError("nonfinite model activations")
        return result
    finally:
        for handle in handles:
            handle.remove()


def candidate_logps(logits, output_ids):
    if len(logits) != len(output_ids) or not output_ids:
        raise ValueError("raw generation logits and output token lengths differ")
    return [float(torch.log_softmax(logit[0].float(), -1)[token].item())
            for logit, token in zip(logits, output_ids, strict=True)]


class HFRunner:
    def __init__(self, config, *, allow_cpu=False, local_files_only=False):
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if config["dtype"] != "float16":
            raise ValueError("registered dtype is float16")
        self.config = dict(config)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if self.device == "cpu" and not allow_cpu:
            raise RuntimeError("CUDA unavailable; use free Colab or explicit CPU-only smoke")
        for field in ("model_revision", "tokenizer_revision"):
            value = config[field]
            if len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError(f"{field} must be an immutable commit")
        self.tokenizer = AutoTokenizer.from_pretrained(
            config["model_id"], revision=config["tokenizer_revision"],
            local_files_only=local_files_only, trust_remote_code=False)
        self.model = AutoModelForCausalLM.from_pretrained(
            config["model_id"], revision=config["model_revision"],
            dtype=torch.float16, device_map={"": self.device},
            local_files_only=local_files_only, trust_remote_code=False)
        self.model.eval().requires_grad_(False)
        self.layers = self.model.model.layers
        self.identity = {**runtime_identity(), "model_id": config["model_id"],
                         "model_revision": config["model_revision"],
                         "tokenizer_revision": config["tokenizer_revision"],
                         "dtype": "float16", "device": self.device,
                         "chat_template_sha256": hashlib.sha256(
                             self.tokenizer.chat_template.encode()).hexdigest(),
                         "n_layers": len(self.layers)}

    def synchronize(self):
        if self.device == "cuda":
            torch.cuda.synchronize()

    def generate(self, task, seed, remaining, *, capture=True):
        from transformers import StoppingCriteria, StoppingCriteriaList

        if remaining <= 0:
            raise TimeoutError("no generation budget remains")
        self.synchronize()
        start = time.monotonic()
        deadline = start + remaining
        class Deadline(StoppingCriteria):
            def __call__(self, input_ids, scores, **kwargs):
                return time.monotonic() >= deadline
        ids = encode_prompt(self.tokenizer, task["prompt"], self.config["max_input_tokens"])
        devices = [torch.cuda.current_device()] if self.device == "cuda" else []
        with torch.random.fork_rng(devices=devices), torch.inference_mode():
            torch.manual_seed(seed)
            outputs = self.model.generate(
                input_ids=torch.tensor([ids], device=self.device),
                attention_mask=torch.ones((1, len(ids)), dtype=torch.long, device=self.device),
                do_sample=True, temperature=self.config["temperature"],
                top_p=self.config["top_p"], max_new_tokens=self.config["max_new_tokens"],
                stopping_criteria=StoppingCriteriaList([Deadline()]),
                return_dict_in_generate=True, output_logits=True,
                pad_token_id=self.tokenizer.pad_token_id)
        output_ids = outputs.sequences[0, len(ids):].tolist()
        logps = candidate_logps(outputs.logits, output_ids)
        text = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        del outputs
        self.synchronize()
        generation_s = time.monotonic() - start
        result = dict(text=text, input_ids=ids, output_ids=output_ids,
                      prompt_sha256=hashlib.sha256(task["prompt"].encode()).hexdigest(),
                      sum_logp=sum(logps), mean_logp=sum(logps)/len(logps),
                      token_logps=logps, generation_s=generation_s,
                      extraction_s=0., seed=seed, answer_start=0,
                      answer_end=len(output_ids))
        if capture and time.monotonic() < deadline:
            before = time.monotonic()
            # Replay is charged. This captures states after consuming each token,
            # not the preceding states that generated those tokens.
            all_states = capture_states(self.model, self.layers, ids+output_ids,
                                        list(range(len(ids)-1, len(ids)+len(output_ids))),
                                        device=self.device)
            result["activations"] = all_states[1:]
            result["prompt_boundary"] = all_states[0]
            self.synchronize()
            result["extraction_s"] = time.monotonic()-before
        result["elapsed_s"] = time.monotonic()-start
        result["deadline_exceeded"] = time.monotonic() > deadline
        return result
