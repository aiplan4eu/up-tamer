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
TAMERCOMMIT="ed3e21b306a37ac0045c2310ad1e26021f40865f"

cd ${DIR}/

rm -rf Tamer Tamer.zip
wget https://es-static.fbk.eu/people/amicheli/tamer/aiplan4eu/Tamer-${TAMERCOMMIT}.zip &> /dev/null
unzip Tamer-${TAMERCOMMIT}.zip &> /dev/null
rm Tamer-${TAMERCOMMIT}.zip

python3 ${DIR}/install.py

rm -rf Tamer
