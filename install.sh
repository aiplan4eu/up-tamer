#!/bin/bash
# Copyright 2021 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd ${DIR}/

rm -rf Tamer Tamer.zip
wget https://es-static.fbk.eu/people/amicheli/tamer/aiplan4eu/Tamer.zip &> /dev/null
unzip Tamer.zip &> /dev/null
rm Tamer.zip

python3 ${DIR}/install.py

rm -rf Tamer
