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

# packages/shared/src/postgres_lib/repositories/types.py
from typing import TypeVar
from ..models import Base


ModelType = TypeVar("ModelType", bound=Base)
"""
Generic type variable representing any SQLAlchemy ORM model inheriting from Base.

Used to parameterize repository and service interfaces while preserving static
type safety across different entity types. The bound constraint restricts valid
substitutions to subclasses of the application declarative base.
"""