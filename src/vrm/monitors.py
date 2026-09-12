"""Offline monitors of frozen activations; no base-model weights are loaded here.

Bundles contain metadata.json and model.pt or model.pkl. Only load trusted
bundles: the sklearn payload uses pickle. See the implementation document for
the Three-Reader adaptation's fidelity limits.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import pickle
from typing import Any, Mapping, Sequence

import numpy as np
from scipy import sparse
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.preprocessing import StandardScaler
import torch
from torch import Tensor, nn
from torch.nn import functional as F
from torch.nn.utils.rnn import pack_sequence


Record = Mapping[str, Any]
SEEDS = (11, 22, 33)
C_GRID = (0.01, 0.1, 1.0, 10.0)
PAPER_URL = "https://arxiv.org/html/2608.05660v1"
BASELINE_NAMES = ("static_all_layers", "text", "likelihood", "sum_logp", "mean_logp")


def _activations(record: Record, shape: tuple[int, int] | None = None) -> np.ndarray:
    try:
        x = np.asarray(record["activations"], dtype=np.float32)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("activations must be a finite [token, layer, hidden] array") from exc
    if x.ndim != 3 or x.shape[0] < 1 or x.shape[1] < 2 or x.shape[2] < 1:
        raise ValueError("activations must have shape [T>=1, L>=2, D>=1]")
    if shape is not None and x.shape[1:] != shape:
        raise ValueError(f"activation layer/hidden shape differs from {shape}")
    if not np.isfinite(x).all():
        raise ValueError("activations must be finite")
    return x


def _span(record: Record, length: int) -> tuple[int, int]:
    start, end = record.get("answer_start", 0), record.get("answer_end", length)
    if (not isinstance(start, (int, np.integer)) or isinstance(start, bool)
            or not isinstance(end, (int, np.integer)) or isinstance(end, bool)
            or not 0 <= start < end <= length):
        raise ValueError("answer span must satisfy 0 <= answer_start < answer_end <= T")
    return int(start), int(end)


def _number(record: Record, key: str) -> float:
    try:
        value = float(record[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be finite") from exc
    if not math.isfinite(value):
        raise ValueError(f"{key} must be finite")
    return value


def _validate_splits(train: Sequence[Record], val: Sequence[Record]) -> tuple[int, int]:
    if not train or not val:
        raise ValueError("train and validation must both be nonempty")
    shape = _activations(train[0]).shape[1:]
    ids: list[set[str]] = []
    for name, rows, expected in (
        ("train", train, "train"),
        ("val", val, "val"),
    ):
        task_ids = set()
        for row in rows:
            x = _activations(row, shape)
            _span(row, len(x))
            if row.get("label") not in (0, 1):
                raise ValueError("label must be 0 or 1")
            if not isinstance(row.get("text"), str):
                raise ValueError("text must be a string")
            if not isinstance(row.get("task_id"), (str, int)) or str(row["task_id"]) == "":
                raise ValueError("task_id must be a nonempty string or integer")
            if row.get("split") != expected:
                raise ValueError(f"unexpected split in {name}; test records cannot be fitted")
            _number(row, "sum_logp")
            _number(row, "mean_logp")
            task_ids.add(str(row["task_id"]))
        ids.append(task_ids)
    if ids[0] & ids[1]:
        raise ValueError("train and validation task_id overlap")
    if set(row["label"] for row in train) != {0, 1}:
        raise ValueError("training requires both label classes")
    return shape


def relative_layer_sites(n_layers: int) -> tuple[int, ...]:
    """Six relative post-block depths, rounded half up, returned zero-based."""
    if n_layers < 6:
        raise ValueError("six distinct layer sites require at least 6 layers")
    return tuple(int(math.floor(n_layers * fraction / 8 + 0.5)) - 1
                 for fraction in (2, 3, 4, 5, 6, 7))


def static_features(record: Record) -> np.ndarray:
    """Concatenate separately unit-normalized final-token states at ALL layers."""
    x = _activations(record)[-1].astype(np.float64)
    norm = np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-12)
    return (x / norm).reshape(-1)


def motion_sequence(activations: Tensor) -> Tensor:
    """Token-major, depth-minor raw adjacent-post-block differences, no BOS pad."""
    if activations.ndim != 3 or activations.shape[0] < 1 or activations.shape[1] < 2:
        raise ValueError("motion needs nonempty [token, layer>=2, hidden] states")
    return (activations[:, 1:] - activations[:, :-1]).reshape(-1, activations.shape[-1])


class MotionReader(nn.Module):
    def __init__(self, hidden_dim: int):
        super().__init__()
        self.lstm = nn.LSTM(hidden_dim, 128, num_layers=2, bidirectional=True,
                            batch_first=True)

    def forward(self, activations: Sequence[Tensor]) -> Tensor:
        if not activations:
            raise ValueError("empty activation batch")
        packed = pack_sequence([motion_sequence(x) for x in activations], enforce_sorted=False)
        _, (hidden, _) = self.lstm(packed)
        # h_n contains both true sequence endpoints, including the backward start.
        return torch.cat((hidden[-2], hidden[-1]), dim=-1)


class EMACodebook(nn.Module):
    """Hard VQ with straight-through gradients and train-only EMA buffers."""

    def __init__(self, dimension: int, size: int = 128, decay: float = 0.99,
                 dead_steps: int = 100):
        super().__init__()
        if dimension < 1 or size < 1 or not 0 <= decay < 1 or dead_steps < 1:
            raise ValueError("invalid codebook configuration")
        self.size, self.decay, self.dead_steps = size, decay, dead_steps
        self.register_buffer("embedding", torch.zeros(size, dimension))
        self.register_buffer("ema_count", torch.zeros(size))
        self.register_buffer("ema_sum", torch.zeros(size, dimension))
        self.register_buffer("unused_steps", torch.zeros(size, dtype=torch.long))
        self.register_buffer("initialized", torch.tensor(False))

    def _sample(self, z: Tensor, count: int) -> Tensor:
        order = torch.randperm(len(z), device=z.device)
        return z[order[torch.arange(count, device=z.device) % len(z)]]

    @torch.no_grad()
    def _initialize(self, z: Tensor) -> None:
        self.embedding.copy_(self._sample(z, self.size))
        self.ema_sum.copy_(self.embedding)
        self.ema_count.fill_(1)
        self.initialized.fill_(True)

    @torch.no_grad()
    def _update(self, z: Tensor, indices: Tensor) -> None:
        count = torch.bincount(indices, minlength=self.size).to(z.dtype)
        sums = torch.zeros_like(self.ema_sum).index_add_(0, indices, z)
        self.ema_count.mul_(self.decay).add_(count, alpha=1 - self.decay)
        self.ema_sum.mul_(self.decay).add_(sums, alpha=1 - self.decay)
        self.embedding.copy_(self.ema_sum / self.ema_count.clamp_min(1e-8).unsqueeze(1))
        self.unused_steps.add_(1)
        self.unused_steps[count > 0] = 0
        dead = self.unused_steps >= self.dead_steps
        if dead.any():
            replacements = self._sample(z, int(dead.sum().item()))
            self.embedding[dead] = replacements
            self.ema_sum[dead] = replacements
            self.ema_count[dead] = 1
            self.unused_steps[dead] = 0

    def forward(self, z: Tensor) -> tuple[Tensor, Tensor]:
        if z.ndim != 2 or len(z) == 0 or z.shape[1] != self.embedding.shape[1]:
            raise ValueError("codebook expects nonempty [batch, code_dimension]")
        if not self.initialized.item():
            if not self.training:
                raise RuntimeError("codebook must be initialized on training data before evaluation")
            self._initialize(z.detach())
        distance = (z.detach().square().sum(1, keepdim=True)
                    + self.embedding.square().sum(1) - 2 * z.detach() @ self.embedding.T)
        indices = distance.argmin(dim=1)
        quantized = self.embedding[indices].detach().clone()
        commitment = F.mse_loss(z, quantized)
        if self.training:
            self._update(z.detach(), indices)
        # Exact code vectors in the forward pass, identity Jacobian for the encoder.
        return quantized + (z - z.detach()), commitment


class _StateReader(nn.Module):
    def __init__(self, n_layers: int, hidden_dim: int, projection_dim: int):
        super().__init__()
        self.sites = relative_layer_sites(n_layers)
        self.projection = nn.Linear(hidden_dim, projection_dim, bias=False)

    def projected(self, x: Tensor, span: tuple[int, int]) -> Tensor:
        start, end = span
        if not 0 <= start < end <= len(x):
            raise ValueError("invalid answer span")
        x = x[max(start, end - 64):end, self.sites, :]
        return self.projection(F.normalize(x, dim=-1, eps=1e-12)).flatten(1)


class DirectionReader(_StateReader):
    def __init__(self, n_layers: int, hidden_dim: int):
        super().__init__(n_layers, hidden_dim, 8)
        self.mlp = nn.Sequential(nn.Linear(48, 32), nn.ReLU(), nn.Linear(32, 32))
        self.combine = nn.Linear(64, 32)

    def forward(self, activations: Sequence[Tensor], spans: Sequence[tuple[int, int]]) -> Tensor:
        summaries = []
        for x, span in zip(activations, spans, strict=True):
            p = self.mlp(self.projected(x, span))
            summaries.append(torch.cat((p[-1], p.mean(0))))
        return self.combine(torch.stack(summaries))


class RegionReader(_StateReader):
    def __init__(self, n_layers: int, hidden_dim: int, decay: float = 0.99,
                 dead_steps: int = 100):
        super().__init__(n_layers, hidden_dim, 64)
        self.encoder = nn.Sequential(nn.Linear(384, 32), nn.ReLU(), nn.Linear(32, 32))
        self.codebook = EMACodebook(32, size=128, decay=decay, dead_steps=dead_steps)

    def forward(self, activations: Sequence[Tensor],
                spans: Sequence[tuple[int, int]]) -> tuple[Tensor, Tensor]:
        last = torch.stack([self.projected(x, span)[-1]
                            for x, span in zip(activations, spans, strict=True)])
        return self.codebook(self.encoder(last))


class ThreeReader(nn.Module):
    def __init__(self, n_layers: int, hidden_dim: int, *, motion_only: bool = False,
                 ema_decay: float = 0.99, dead_steps: int = 100):
        super().__init__()
        self.n_layers, self.hidden_dim = n_layers, hidden_dim
        self.motion_only = motion_only
        self.motion = MotionReader(hidden_dim)
        if not motion_only:
            self.direction = DirectionReader(n_layers, hidden_dim)
            self.region = RegionReader(n_layers, hidden_dim, ema_decay, dead_steps)
        self.head = nn.Sequential(nn.Linear(256 if motion_only else 320, 128),
                                  nn.ReLU(), nn.Linear(128, 1))

    def forward(self, activations: Sequence[Tensor],
                spans: Sequence[tuple[int, int]] | None = None) -> tuple[Tensor, Tensor]:
        if not activations:
            raise ValueError("empty activation batch")
        if any(x.ndim != 3 or x.shape[1:] != (self.n_layers, self.hidden_dim)
               or len(x) == 0 for x in activations):
            raise ValueError("unexpected activation shape")
        if spans is None:
            spans = [(0, len(x)) for x in activations]
        motion = self.motion(activations)
        commitment = motion.new_zeros(())
        streams = [motion]
        if not self.motion_only:
            region, commitment = self.region(activations, spans)
            streams.extend((self.direction(activations, spans), region))
        return self.head(torch.cat(streams, dim=-1)).squeeze(-1), commitment


@dataclass(frozen=True)
class TrainingConfig:
    max_epochs: int = 10
    patience: int = 2
    min_delta: float = 0.0
    batch_size: int = 8
    accumulation_steps: int = 1
    learning_rate: float = 1e-3
    commitment_weight: float = 0.25

    def __post_init__(self) -> None:
        if not 1 <= self.max_epochs <= 10:
            raise ValueError("max_epochs must be between 1 and 10")
        if self.patience < 1 or self.batch_size < 1 or self.accumulation_steps < 1:
            raise ValueError("patience, batch_size and accumulation_steps must be positive")
        if self.min_delta < 0 or self.learning_rate <= 0 or self.commitment_weight < 0:
            raise ValueError("invalid training configuration")


class _StaticFeatures:
    def fit(self, rows: Sequence[Record]) -> "_StaticFeatures":
        return self

    def transform(self, rows: Sequence[Record]) -> np.ndarray:
        return np.stack([static_features(row) for row in rows])


class _LikelihoodFeatures:
    def __init__(self) -> None:
        self.scaler = StandardScaler()

    @staticmethod
    def _raw(rows: Sequence[Record]) -> np.ndarray:
        return np.asarray(
            [[_number(row, "sum_logp"), _number(row, "mean_logp")] for row in rows],
            dtype=np.float64,
        )

    def fit(self, rows: Sequence[Record]) -> "_LikelihoodFeatures":
        self.scaler.fit(self._raw(rows))
        return self

    def transform(self, rows: Sequence[Record]) -> np.ndarray:
        return self.scaler.transform(self._raw(rows))


class _TextFeatures:
    def __init__(self) -> None:
        self.vectorizer: TfidfVectorizer | None = None
        self.scaler = StandardScaler()

    @staticmethod
    def _numeric(rows: Sequence[Record]) -> np.ndarray:
        return np.asarray([
            [len(row["text"]), len(row["text"].split()),
             _number(row, "sum_logp"), _number(row, "mean_logp")]
            for row in rows
        ], dtype=np.float64)

    def fit(self, rows: Sequence[Record]) -> "_TextFeatures":
        texts = [row["text"] for row in rows]
        self.vectorizer = (
            TfidfVectorizer()
            if any(text.strip() for text in texts)
            else TfidfVectorizer(vocabulary={"__empty__": 0})
        )
        self.vectorizer.fit(texts)
        self.scaler.fit(self._numeric(rows))
        return self

    def transform(self, rows: Sequence[Record]):
        if self.vectorizer is None:
            raise RuntimeError("text feature map is not fitted")
        text = self.vectorizer.transform([row["text"] for row in rows])
        numeric = sparse.csr_matrix(self.scaler.transform(self._numeric(rows)))
        return sparse.hstack((text, numeric), format="csr")


class _LinearMonitor:
    def __init__(self, name: str, features, estimator, metadata: Mapping[str, Any]):
        self.name = name
        self.features = features
        self.estimator = estimator
        self.metadata = dict(metadata)

    def predict(self, rows: Sequence[Record]) -> np.ndarray:
        return self.estimator.predict_proba(self.features.transform(rows))[:, 1]

    def score(self, row: Record) -> float:
        return float(self.predict([row])[0])


class _RawMonitor:
    def __init__(self, name: str):
        self.name = name
        self.metadata = {"name": name, "score_kind": "raw_log_probability"}

    def predict(self, rows: Sequence[Record]) -> np.ndarray:
        return np.asarray([_number(row, self.name) for row in rows], dtype=np.float64)

    def score(self, row: Record) -> float:
        return float(_number(row, self.name))


class _NeuralMonitor:
    def __init__(self, model: ThreeReader, metadata: Mapping[str, Any]):
        self.model = model.eval()
        self.metadata = dict(metadata)

    def predict(self, rows: Sequence[Record]) -> np.ndarray:
        tensors = [torch.as_tensor(_activations(row), dtype=torch.float32) for row in rows]
        spans = [_span(row, len(tensor)) for row, tensor in zip(rows, tensors, strict=True)]
        with torch.inference_mode():
            logits, _ = self.model(tensors, spans)
        return torch.sigmoid(logits).cpu().numpy()

    def score(self, row: Record) -> float:
        return float(self.predict([row])[0])


def _labels(rows: Sequence[Record]) -> np.ndarray:
    return np.asarray([int(row["label"]) for row in rows], dtype=np.int64)


def _write_bundle(path: Path, monitor, metadata: Mapping[str, Any]) -> None:
    path.mkdir(parents=False, exist_ok=False)
    (path / "metadata.json").write_text(
        json.dumps(dict(metadata), sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    if isinstance(monitor, _NeuralMonitor):
        torch.save(monitor.model.state_dict(), path / "model.pt")
    else:
        with (path / "model.pkl").open("wb") as handle:
            pickle.dump(monitor, handle)


def _fit_linear(name: str, features, train: Sequence[Record], val: Sequence[Record]):
    features.fit(train)
    train_x, val_x = features.transform(train), features.transform(val)
    train_y, val_y = _labels(train), _labels(val)
    candidates = []
    for regularization in C_GRID:
        estimator = LogisticRegression(
            C=regularization, max_iter=1000, random_state=11, solver="liblinear"
        ).fit(train_x, train_y)
        probability = estimator.predict_proba(val_x)[:, 1]
        candidates.append((log_loss(val_y, probability, labels=[0, 1]), regularization,
                           estimator))
    loss, selected, estimator = min(candidates, key=lambda item: (item[0], item[1]))
    metadata = {
        "name": name,
        "kind": "linear_probability",
        "selected_C": selected,
        "validation_logloss": float(loss),
        "sklearn_version": sklearn.__version__,
    }
    return _LinearMonitor(name, features, estimator, metadata), metadata


def _fit_baselines(train: Sequence[Record], val: Sequence[Record], output: Path) -> list[str]:
    names = []
    for name, features in (
        ("static_all_layers", _StaticFeatures()),
        ("text", _TextFeatures()),
        ("likelihood", _LikelihoodFeatures()),
    ):
        monitor, metadata = _fit_linear(name, features, train, val)
        _write_bundle(output / name, monitor, metadata)
        names.append(name)
    for name in ("sum_logp", "mean_logp"):
        monitor = _RawMonitor(name)
        _write_bundle(output / name, monitor, monitor.metadata)
        names.append(name)
    return names


def _fallback_count(rows: Sequence[Record]) -> int:
    return sum("answer_start" not in row or "answer_end" not in row for row in rows)


def _predict_neural(model: ThreeReader, rows: Sequence[Record]) -> np.ndarray:
    return _NeuralMonitor(model, {}).predict(rows)


def _fit_one_neural(kind: str, seed: int, train: Sequence[Record], val: Sequence[Record],
                    config: TrainingConfig) -> tuple[_NeuralMonitor, dict[str, Any]]:
    torch.manual_seed(seed)
    n_layers, hidden_dim = _activations(train[0]).shape[1:]
    model = ThreeReader(n_layers, hidden_dim, motion_only=kind == "motion")
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    best_state = None
    best_loss = math.inf
    best_epoch = 0
    stale = 0
    history = []
    labels = _labels(train)
    for epoch in range(1, config.max_epochs + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        for start in range(0, len(train), config.batch_size):
            rows = train[start:start + config.batch_size]
            tensors = [torch.as_tensor(_activations(row), dtype=torch.float32) for row in rows]
            spans = [_span(row, len(x)) for row, x in zip(rows, tensors, strict=True)]
            logits, commitment = model(tensors, spans)
            target = torch.as_tensor(labels[start:start + len(rows)], dtype=torch.float32)
            loss = F.binary_cross_entropy_with_logits(logits, target)
            loss = loss + config.commitment_weight * commitment
            (loss / config.accumulation_steps).backward()
            last_batch = start + config.batch_size >= len(train)
            step_number = start // config.batch_size + 1
            if step_number % config.accumulation_steps == 0 or last_batch:
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
        model.eval()
        probabilities = _predict_neural(model, val)
        val_loss = float(log_loss(_labels(val), probabilities, labels=[0, 1]))
        history.append({"epoch": epoch, "val_logloss": val_loss})
        if val_loss < best_loss - config.min_delta:
            best_loss = val_loss
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            stale = 0
        else:
            stale += 1
            if stale >= config.patience:
                break
    if best_state is None:
        raise RuntimeError("neural training produced no checkpoint")
    model.load_state_dict(best_state)
    model.eval()
    metadata = {
        "name": f"{kind}_seed{seed}",
        "kind": kind,
        "seed": seed,
        "n_layers": n_layers,
        "hidden_dim": hidden_dim,
        "training_config": asdict(config),
        "history": history,
        "best_epoch": best_epoch,
        "answer_span_fallback_count": {
            "train": _fallback_count(train), "val": _fallback_count(val)
        },
        "torch_version": torch.__version__,
        "paper_url": PAPER_URL,
    }
    return _NeuralMonitor(model, metadata), metadata


def _fit_neural(train: Sequence[Record], val: Sequence[Record], output: Path,
                config: TrainingConfig, seeds: Sequence[int],
                kinds: Sequence[str]) -> list[str]:
    if any(kind not in ("motion", "three_reader") for kind in kinds):
        raise ValueError("unknown neural monitor kind")
    names = []
    for kind in kinds:
        for seed in seeds:
            monitor, metadata = _fit_one_neural(kind, int(seed), train, val, config)
            name = metadata["name"]
            _write_bundle(output / name, monitor, metadata)
            names.append(name)
    return names


def fit_neural_monitors(train: Sequence[Record], val: Sequence[Record], output_dir,
                        *, config: TrainingConfig | None = None,
                        seeds: Sequence[int] = SEEDS,
                        kinds: Sequence[str] = ("motion", "three_reader")) -> list[str]:
    _validate_splits(train, val)
    output = Path(output_dir)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"output directory already exists: {output}")
    output.mkdir(parents=True, exist_ok=True)
    return _fit_neural(train, val, output, config or TrainingConfig(), seeds, kinds)


def fit_monitors(train: Sequence[Record], val: Sequence[Record], output_dir, *,
                 neural: bool = True, config: TrainingConfig | None = None) -> list[str]:
    _validate_splits(train, val)
    output = Path(output_dir)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"output directory already exists: {output}")
    output.mkdir(parents=True, exist_ok=True)
    names = _fit_baselines(train, val, output)
    if neural:
        names.extend(_fit_neural(train, val, output, config or TrainingConfig(),
                                 SEEDS, ("motion", "three_reader")))
    return names


def load_monitor(path) -> _LinearMonitor | _RawMonitor | _NeuralMonitor:
    bundle = Path(path)
    metadata = json.loads((bundle / "metadata.json").read_text(encoding="utf-8"))
    model_path = bundle / "model.pt"
    if model_path.exists():
        kind = metadata["kind"]
        model = ThreeReader(
            int(metadata["n_layers"]), int(metadata["hidden_dim"]),
            motion_only=kind == "motion",
        )
        model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
        return _NeuralMonitor(model, metadata)
    with (bundle / "model.pkl").open("rb") as handle:
        monitor = pickle.load(handle)
    monitor.metadata = metadata
    return monitor
