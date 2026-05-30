# Copyright (c) 2026 Ilya Snegov (aka Sierra Arn)

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# app/workers/task_infra/tensors_io.py
"""
Serialization utilities for PipelineOutput using the safetensors format.

This module provides functions to convert nested inference results into a flat
dictionary of CPU tensors suitable for safetensors serialization, and to
reconstruct the original nested structure from the archived data. The format
uses dot-separated keys to encode the hierarchy and stores reconstruction
metadata (total frame count and valid indices) as JSON strings in the
safetensors header.

The serialization is designed for interoperability between inference and
visualization tasks. Tensors are moved to CPU and made contiguous before
saving. Shared memory references are broken via cloning to ensure safe
archiving. The format is versioned via the structure_version metadata field.

Usage
-----
from pathlib import Path
from app.workers.task_infra.tensors_io import save_pipeline_output, load_pipeline_output

path = save_pipeline_output(pipeline_output)
restored = load_pipeline_output(path)
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Any
import torch
from safetensors import safe_open
from safetensors.torch import save_file
from ensam3d_inference import FramePoseResult, PipelineOutput
from ensam3d_inference.core import PoseEstimatorOutput
from ensam3d_inference.preprocessor.detector import Detection


def _ensure_cpu_contiguous(tensor: torch.Tensor) -> torch.Tensor:
    """
    Move tensor to CPU memory and ensure contiguous layout for serialization.

    Parameters
    ----------
    tensor : torch.Tensor
        Input tensor potentially located on CUDA or non-contiguous memory.

    Returns
    -------
    torch.Tensor
        Tensor on CPU with contiguous memory layout.
    """
    if not tensor.is_contiguous():
        tensor = tensor.contiguous()
    return tensor.cpu()


def _flatten_to_dict(obj: Any, prefix: str = "") -> dict[str, torch.Tensor]:
    """
    Recursively convert nested NamedTuples, lists, and tensors to a flat dict.

    Traverses the input structure depth-first. NamedTuples are expanded using
    their _fields attribute. Lists and tuples are indexed numerically. Tensors
    are moved to CPU and made contiguous before insertion. The resulting keys
    use dot-separated notation to encode the path from root to leaf.

    Parameters
    ----------
    obj : Any
        Nested structure containing tensors, NamedTuples, lists, or None.
    prefix : str, optional
        Current key path for recursive calls. Default is empty string for root.

    Returns
    -------
    dict of str to torch.Tensor
        Flattened dictionary mapping dot-separated keys to CPU tensors.
        Empty dict if obj is None or contains no tensors.

    Notes
    -----
    NamedTuple detection relies on the _fields attribute. This is compatible
    with typing.NamedTuple and collections.namedtuple. Primitive types other
    than tensors are silently ignored during flattening.
    """
    result: dict[str, torch.Tensor] = {}

    if obj is None:
        return result

    if isinstance(obj, torch.Tensor):
        result[prefix] = _ensure_cpu_contiguous(obj)
        return result

    if isinstance(obj, tuple) and hasattr(obj, "_fields"):
        for field_name in obj._fields:
            value = getattr(obj, field_name)
            child_prefix = f"{prefix}.{field_name}" if prefix else field_name
            result.update(_flatten_to_dict(value, child_prefix))
        return result

    if isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            child_prefix = f"{prefix}.{i}" if prefix else str(i)
            result.update(_flatten_to_dict(item, child_prefix))
        return result

    return result


def _reconstruct_from_dict(
    data: dict[str, torch.Tensor],
    metadata: dict[str, str],
) -> PipelineOutput:
    """
    Reconstruct nested PipelineOutput from flat tensor dict and metadata.

    Uses the total_frames and valid_indices fields from metadata to allocate
    the output list. For each valid index, extracts tensors with the matching
    frame prefix and rebuilds Detection and PoseEstimatorOutput instances.
    Missing frames remain None to preserve alignment with the original input.

    Parameters
    ----------
    data : dict of str to torch.Tensor
        Flat dictionary loaded from safetensors. Keys use dot-separated
        notation encoding the original nested structure.
    metadata : dict of str to str
        Reconstruction metadata. Must contain total_frames (integer as string)
        and valid_indices (JSON-encoded list of integers).

    Returns
    -------
    PipelineOutput
        Nested list of FramePoseResult or None matching the original structure.
        Length equals total_frames from metadata.

    Raises
    ------
    ValueError
        If required metadata fields are missing or malformed, or if expected
        tensor keys are absent for a valid frame index.

    Notes
    -----
    The reconstruction assumes the key format frame_{idx}.detection.coords,
    frame_{idx}.detection.confidence, and frame_{idx}.pose.{field_name} for
    each pose output field. This format is produced by _flatten_to_dict and
    must not be modified externally. The confidence tensor is kept as a
    torch.Tensor rather than unwrapped to a scalar to preserve type consistency
    with the original PipelineOutput; callers such as render_frame expect to
    call .detach().cpu().numpy() on it directly.
    """
    try:
        total_frames: int = int(metadata.get("total_frames", "0"))
        valid_indices: list[int] = json.loads(metadata.get("valid_indices", "[]"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid reconstruction metadata: {exc}") from exc

    results: PipelineOutput = [None] * total_frames

    for idx in valid_indices:
        prefix = f"{idx}."
        frame_tensors = {k: v for k, v in data.items() if k.startswith(prefix)}

        if not frame_tensors:
            continue

        coords_key = f"{prefix}detection.coords"
        conf_key = f"{prefix}detection.confidence"

        if coords_key not in frame_tensors or conf_key not in frame_tensors:
            raise ValueError(f"Missing detection tensors for frame {idx}")

        coords = frame_tensors[coords_key]
        confidence = frame_tensors[conf_key]
        detection = Detection(coords=coords, confidence=confidence)

        pose_data: dict[str, torch.Tensor] = {}
        pose_prefix = f"{prefix}pose."
        for key, tensor in frame_tensors.items():
            if key.startswith(pose_prefix):
                field_name = key[len(pose_prefix):]
                pose_data[field_name] = tensor

        if not pose_data:
            raise ValueError(f"Missing pose tensors for frame {idx}")

        pose = PoseEstimatorOutput(**pose_data)
        results[idx] = FramePoseResult(detection=detection, pose=pose)

    return results


def _clone_tensors(obj: Any) -> Any:
    """
    Recursively clone all torch.Tensor instances in a nested structure.

    Breaks shared memory references to ensure safetensors can serialize
    the data without duplicates or ambiguity. Non-tensor objects are returned
    unchanged.

    Parameters
    ----------
    obj : Any
        Input object (dict, list, tuple, tensor, or primitive).

    Returns
    -------
    Any
        Deep copy with all tensors cloned. Structure and non-tensor values
        are preserved.
    """
    if isinstance(obj, torch.Tensor):
        return obj.clone()
    if isinstance(obj, dict):
        return {k: _clone_tensors(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return type(obj)(_clone_tensors(item) for item in obj)
    return obj


def save_pipeline_output(output: PipelineOutput, path: Path | None = None) -> Path:
    """
    Serialize PipelineOutput to a safetensors archive.

    Flattens the nested structure to a dict of CPU tensors, clones tensors
    to break shared references, and writes the archive with reconstruction
    metadata. If no path is provided, a temporary file is created in the
    system temp directory.

    Parameters
    ----------
    output : PipelineOutput
        Inference results to serialize. Must be non-empty.
    path : Path or None, optional
        Destination filesystem path. If None, a temporary file is created.
        Default is None.

    Returns
    -------
    Path
        Path to the created safetensors file.

    Raises
    ------
    ValueError
        If output is empty or if the target path already exists outside
        the system temp directory.
    OSError
        If the temporary file cannot be created or the archive cannot be
        written.

    Notes
    -----
    The archive includes metadata fields total_frames, valid_indices, and
    structure_version. The structure_version field enables forward-compatible
    deserialization if the output format evolves.
    """
    if not output:
        raise ValueError("Cannot save empty pipeline output.")

    if path is None:
        fd, tmp_path = tempfile.mkstemp(suffix=".safetensors", prefix="ensam3d_")
        os.close(fd)
        path = Path(tmp_path)

    if path.exists() and not str(path).startswith(("/tmp", tempfile.gettempdir())):
        raise ValueError(f"Output file already exists: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    flat_tensors = _flatten_to_dict(output)
    flat_tensors = _clone_tensors(flat_tensors)

    valid_indices = [i for i, item in enumerate(output) if item is not None]
    metadata = {
        "total_frames": str(len(output)),
        "valid_indices": json.dumps(valid_indices),
        "structure_version": "1",
    }

    save_file(flat_tensors, str(path), metadata=metadata)
    return path


def load_pipeline_output(path: Path) -> PipelineOutput:
    """
    Reconstruct PipelineOutput from a safetensors archive.

    Reads flat tensor data and embedded metadata to restore the original
    nested list structure with None placeholders for empty frames.

    Parameters
    ----------
    path : Path
        Filesystem path to the safetensors archive.

    Returns
    -------
    PipelineOutput
        Reconstructed nested list matching the original inference output.

    Raises
    ------
    FileNotFoundError
        If the safetensors file does not exist.
    ValueError
        If metadata is missing, malformed, or reconstruction fails due to
        missing tensor keys.
    RuntimeError
        If safetensors reports an I/O or format error during loading.
    """
    if not path.exists():
        raise FileNotFoundError(f"Result file not found: {path}")

    try:
        with safe_open(str(path), framework="pt", device="cpu") as f:
            metadata = f.metadata()
            if "total_frames" not in metadata or "valid_indices" not in metadata:
                raise ValueError("Corrupted file: missing reconstruction metadata.")

            flat_data = {key: f.get_tensor(key) for key in f.keys()}
            return _reconstruct_from_dict(flat_data, metadata)
    except Exception as exc:
        if isinstance(exc, (FileNotFoundError, ValueError)):
            raise
        raise RuntimeError(f"Failed to load safetensors archive: {exc}") from exc