import numpy as np
import pytest
import torch

from vrm.runtime import encode_prompt, capture_states, runtime_identity, candidate_logps


class Tokenizer:
    bos_token_id = 2
    chat_template = "fixed-template"
    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert tokenize is True and add_generation_prompt is True
        return [2, 10, 11]


def test_prompt_uses_template_tokenization_once():
    ids = encode_prompt(Tokenizer(), "goal")
    assert ids == [2, 10, 11]
    with pytest.raises(ValueError, match="limit"):
        encode_prompt(Tokenizer(), "goal", limit=2)


def test_prompt_accepts_real_tokenizer_batch_encoding_shape():
    class BatchTokenizer(Tokenizer):
        def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
            return {"input_ids": [2, 10, 11], "attention_mask": [1, 1, 1]}

    assert encode_prompt(BatchTokenizer(), "goal") == [2, 10, 11]


def test_duplicate_bos_rejected():
    class Bad(Tokenizer):
        def apply_chat_template(self, *args, **kwargs): return [2, 2, 10]
    with pytest.raises(ValueError, match="BOS"):
        encode_prompt(Bad(), "goal")


class Toy(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = torch.nn.ModuleList([torch.nn.Identity(), torch.nn.Identity()])
    def forward(self, input_ids, **kwargs):
        x = input_ids.float().unsqueeze(-1).repeat(1, 1, 3)
        for layer in self.layers:
            x = layer(x + 1)
        return x


def test_capture_exact_positions_and_cleans_up_hooks():
    model = Toy()
    states = capture_states(model, model.layers, [2, 4, 6, 8], [1, 2, 3], device="cpu")
    assert states.shape == (3, 2, 3)
    assert states.dtype == np.float16
    np.testing.assert_array_equal(states[:, 0, 0], [5, 7, 9])
    np.testing.assert_array_equal(states[:, 1, 0], [6, 8, 10])
    assert all(not m._forward_hooks for m in model.layers)


def test_capture_cleans_up_on_failure():
    model = Toy()
    with pytest.raises(ValueError):
        capture_states(model, model.layers, [2, 3], [9], device="cpu")
    assert all(not m._forward_hooks for m in model.layers)


def test_raw_logits_not_warped_sampling_scores():
    logits = [torch.tensor([[0., 1., 2.]]), torch.tensor([[1., 0., 2.]])]
    values = candidate_logps(logits, [2, 0])
    assert values == pytest.approx([torch.log_softmax(logits[0], -1)[0, 2].item(),
                                   torch.log_softmax(logits[1], -1)[0, 0].item()])
    with pytest.raises(ValueError): candidate_logps(logits, [2])


def test_identity_contains_no_environment_secrets(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "never-export-this")
    result = runtime_identity()
    assert "never-export-this" not in str(result)
    assert "python" in result and "packages" in result
