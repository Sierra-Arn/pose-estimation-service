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

# app/workers/inference/tasks/estimate/metadata_persistor.py
from .....shared.postgres import get_sync_db_session, Estimation


def create_estimation_record(
    video_id: int,
    storage_key: str,
    requested_width: int,
    requested_height: int,
    requested_fps: float,
    skip_start_seconds: float,
    duration_seconds: float,
    description: str | None = None,
) -> int:
    """
    Persist pipeline execution metadata to the database.

    Parameters
    ----------
    video_id : int
        Foreign key referencing the source video record.
    storage_key : str
        Object storage path to the serialized safetensors archive.
    requested_width : int
        Target frame width in pixels applied during preprocessing.
    requested_height : int
        Target frame height in pixels applied during preprocessing.
    requested_fps : float
        Frame sampling rate applied before inference in fps.
    skip_start_seconds : float
        Temporal offset in seconds to skip from video start before processing.
    duration_seconds : float
        Total analyzed segment duration in seconds.
    description : str or None, optional
        Human-readable label for quick identification in listings.
        Default is None.

    Returns
    -------
    int
        Primary key of the newly created ensam3d_result record.
    """
    with get_sync_db_session() as session:
        record = Estimation(
            video_id=video_id,
            storage_key=storage_key,
            requested_width=requested_width,
            requested_height=requested_height,
            requested_fps=requested_fps,
            skip_start_seconds=skip_start_seconds,
            duration_seconds=duration_seconds,
            description=description,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record.id