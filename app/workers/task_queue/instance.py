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

# app/workers/task_queue/instance.py
from kombu import Exchange, Queue
from celery import Celery
from .config import celery_config


tasks_exchange = Exchange(
    celery_config.exchange_name,
    type=celery_config._exchange_type,
)

inference_queue = Queue(
    celery_config.queue_name_inference,
    exchange=tasks_exchange,
    routing_key=celery_config.queue_name_inference,
)

default_queue = Queue(
    celery_config.queue_name_default,
    exchange=tasks_exchange,
    routing_key=celery_config.queue_name_default,
)

celery_app = Celery(
    celery_config.app_name,
    broker=celery_config.broker_url,
    backend=celery_config.result_backend_url,
)

celery_app.conf.update(
    task_serializer=celery_config._task_serializer,
    result_serializer=celery_config._result_serializer,
    accept_content=celery_config._accept_content,
    timezone=celery_config._timezone,
    enable_utc=celery_config._enable_utc,
    result_expires=celery_config.result_expires,
    task_queues=(inference_queue, default_queue),
)

celery_app.autodiscover_tasks(["app.workers.inference.tasks", "app.workers.default.tasks"])