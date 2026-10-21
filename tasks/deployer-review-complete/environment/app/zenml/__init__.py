#  Copyright (c) ZenML GmbH 2025. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.
"""ZenML (relocated Kubernetes-deployer slice).

This is a self-contained subset of the ZenML source tree carrying the Kubernetes
deployer's manifest-rendering path (templates + template engine + the deployer
code that assembles the label/selector context). The live-cluster plumbing that
talks to a real Kubernetes API server is not part of this slice.
"""

__version__ = "0.85.0.dev"
