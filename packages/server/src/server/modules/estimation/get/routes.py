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

# packages/server/src/server/modules/estimation/get/routes.py
from fastapi import status, Path, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from postgres_lib import get_async_db_session, EstimationRepository
from ..schemas import EstimationResponse
from ..router import estimation_router
from ..utils import get_estimation_or_404


@estimation_router.get(
    "/",
    response_model=list[EstimationResponse],
    status_code=status.HTTP_200_OK,
    summary="List estimations",
    description="Retrieves a paginated list of estimation metadata records ordered by primary key.",
)
async def list_estimations_route(
    skip: int = Query(0, ge=0, description="Number of records to offset from the beginning."),
    limit: int = Query(50, gt=0, le=100, description="Maximum number of records to return."),
    session: AsyncSession = Depends(get_async_db_session),
) -> list[EstimationResponse]:
    """
    Fetch a paginated list of estimation records.

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
    list of EstimationResponse
        Ordered list of estimation payloads matching the pagination window.
        Returns an empty list if no records exist in the specified range.
    """
    estimations = await EstimationRepository.get_all(session, skip=skip, limit=limit)
    return [EstimationResponse.model_validate(est) for est in estimations]


@estimation_router.get(
    "/{estimation_id}/",
    response_model=EstimationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get estimation details",
    description="""
        Retrieves configuration parameters, object storage location, and creation metadata 
        for a specific pose analysis result.
    """
)
async def get_estimation_route(
    estimation_id: int = Path(..., description="Primary key of the target estimation record."),
    session: AsyncSession = Depends(get_async_db_session),
) -> EstimationResponse:
    """
    Fetch a single estimation record by primary key.

    Parameters
    ----------
    estimation_id : int
        Primary key of the target estimation in the estimations table.
    session : AsyncSession
        Active asynchronous database session bound to the transaction.

    Returns
    -------
    EstimationResponse
        Structured payload containing pipeline settings, storage key, and metadata.

    Raises
    ------
    HTTPException
        404 Not Found if the estimation ID does not exist in the database.
    """
    estimation = await get_estimation_or_404(session, estimation_id)
    return EstimationResponse.model_validate(estimation)