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

# packages/server/src/server/modules/visualization/get/routes.py
from fastapi import status, Path, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from postgres_lib import get_async_db_session, VisualizationRepository
from ..schemas import VisualizationResponse
from ..router import visualization_router
from ..utils import get_visualization_or_404


@visualization_router.get(
    "/",
    response_model=list[VisualizationResponse],
    status_code=status.HTTP_200_OK,
    summary="List visualizations",
    description="Retrieves a paginated list of visualization metadata records ordered by primary key.",
)
async def list_visualizations_route(
    skip: int = Query(0, ge=0, description="Number of records to offset from the beginning."),
    limit: int = Query(50, gt=0, le=100, description="Maximum number of records to return."),
    session: AsyncSession = Depends(get_async_db_session),
) -> list[VisualizationResponse]:
    """
    Fetch a paginated list of visualization records.

    Parameters
    ----------
    skip : int
        Offset from the start of the result set.
        Default is 0.
    limit : int
        Maximum number of records to return. Capped at 100.
        Default is 50.
    session : AsyncSession
        Active asynchronous database session bound to the transaction.

    Returns
    -------
    list of VisualizationResponse
        Ordered list of visualization payloads matching the pagination window.
        Returns an empty list if no records exist in the specified range.
    """
    visualizations = await VisualizationRepository.get_all(session, skip=skip, limit=limit)
    return [VisualizationResponse.model_validate(vis) for vis in visualizations]


@visualization_router.get(
    "/{visualization_id}/",
    response_model=VisualizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get visualization details",
    description="""
        Retrieves configuration parameters, object storage location, and creation metadata 
        for a specific rendered visualization.
    """
)
async def get_visualization_route(
    visualization_id: int = Path(..., description="Primary key of the target visualization record."),
    session: AsyncSession = Depends(get_async_db_session),
) -> VisualizationResponse:
    """
    Fetch a single visualization record by primary key.

    Parameters
    ----------
    visualization_id : int
        Primary key of the target visualization in the visualizations table.
    session : AsyncSession
        Active asynchronous database session bound to the transaction.

    Returns
    -------
    VisualizationResponse
        Structured payload containing rendering flags, encoding parameters, storage key, and metadata.

    Raises
    ------
    HTTPException
        404 Not Found if the visualization ID does not exist in the database.
    """
    visualization = await get_visualization_or_404(session, visualization_id)
    return VisualizationResponse.model_validate(visualization)