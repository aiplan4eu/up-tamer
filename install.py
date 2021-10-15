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

import os
import shutil
from pysmt.cmd.installers.base import solver_install_site


if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    bindings_dir = os.path.expanduser(solver_install_site(plat_specific=True))

    shutil.copyfile(os.path.join(dir_path, 'Tamer', 'pytamer.py'), os.path.join(bindings_dir, 'pytamer.py'))
    shutil.copyfile(os.path.join(dir_path, 'Tamer', '_pytamer.so'), os.path.join(bindings_dir, '_pytamer.so'))
    print('pytamer installed successfully!')

    if os.path.exists(os.path.join(bindings_dir, 'upf_tamer')):
        shutil.rmtree(os.path.join(bindings_dir, 'upf_tamer'))

    shutil.copytree(os.path.join(dir_path, 'upf_tamer'), os.path.join(bindings_dir, 'upf_tamer'))
    print('upf_tamer installed successfully!')
