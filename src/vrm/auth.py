"""Credential checks only: no model loading, login persistence, or token output."""
import os
import re


class AccessError(RuntimeError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def read_colab_token(get_secret, environment=None):
    """Read the current Secret on every retry; never reuse a stale kernel token."""
    environment = os.environ if environment is None else environment
    environment.pop("HF_TOKEN", None)
    try:
        token = get_secret("HF_TOKEN")
    except Exception:
        raise AccessError("colab_secret_unavailable",
                          "Reconnect Colab, then allow notebook access to HF_TOKEN in Secrets. "
                          "Rerun this cell; do not paste credentials into code or chat.") from None
    if not isinstance(token, str) or not token.strip():
        raise AccessError("colab_secret_unavailable", "Add HF_TOKEN in Colab Secrets.")
    environment["HF_TOKEN"] = token.strip()


def _redacted_failure(exc, stage):
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if status in (401, 403):
        if stage == "identity":
            return AccessError("token_rejected",
                               "HF_TOKEN was rejected (invalid, expired, or revoked). "
                               "Update it in Secrets and rerun authentication.")
        return AccessError("model_access_denied",
                           "Token accepted, but model-file access was denied. Check Gemma "
                           "access and token permissions on huggingface.co/google/gemma-2-2b-it.")
    if status == 404:
        return AccessError("model_revision_unavailable",
                           "Pinned model file or revision unavailable. Do not switch revisions.")
    return AccessError("service_unavailable",
                       "Authentication service or network unavailable. Retry later; "
                       "this is not evidence that the token expired.")


def check_hf_access(config, *, token):
    if not isinstance(token, str) or not token.strip():
        raise AccessError("token_missing", "HF_TOKEN is missing. Read it from Colab Secrets.")
    if config.get("model_id") != "google/gemma-2-2b-it":
        raise ValueError("authentication is scoped to the registered Gemma model")
    for field in ("model_revision", "tokenizer_revision"):
        if not re.fullmatch(r"[0-9a-f]{40}", config.get(field, "")):
            raise ValueError("authentication requires immutable model and tokenizer revisions")
    from huggingface_hub import HfApi, get_hf_file_metadata, hf_hub_url

    try:
        HfApi(endpoint="https://huggingface.co").whoami(token=token, cache=False)
    except Exception as exc:
        raise _redacted_failure(exc, "identity") from None
    files = [("config.json", config["model_revision"]),
             ("model.safetensors.index.json", config["model_revision"]),
             ("tokenizer.json", config["tokenizer_revision"])]
    for filename, revision in files:
        try:
            info = get_hf_file_metadata(
                hf_hub_url(config["model_id"], filename, revision=revision,
                           endpoint="https://huggingface.co"),
                token=token, timeout=10, retry_on_errors=False,
            )
        except Exception as exc:
            raise _redacted_failure(exc, "metadata") from None
        if info.commit_hash != revision:
            raise AccessError("revision_mismatch", "Server returned a different model revision.")
    return {"ready": True, "status": "authenticated_files_accessible",
            "model_id": config["model_id"], "model_revision": config["model_revision"],
            "tokenizer_revision": config["tokenizer_revision"],
            "checked_files": [name for name, _ in files], "model_loaded": False}
