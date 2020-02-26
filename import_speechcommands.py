#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 by David Zurow
# Copyright 2018 by Marc Puels
# Copyright 2016 by G.Bartsch
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#
# convert speechcommands to voxforge-style packages
#

import sys
import os
import codecs
import traceback
import logging
import glob
import re

from optparse               import OptionParser
from nltools                import misc

PROC_TITLE        = 'speechcommands_to_vf'
DEFAULT_NUM_CPUS  = 12

#
# init terminal
#

misc.init_app (PROC_TITLE)

#
# command line
#

parser = OptionParser("usage: %prog [options]")

parser.add_option ("-n", "--num-cpus", dest="num_cpus", type="int", default=DEFAULT_NUM_CPUS,
                   help="number of cpus to use in parallel, default: %d" % DEFAULT_NUM_CPUS)

parser.add_option ("-v", "--verbose", action="store_true", dest="verbose", 
                   help="enable debug output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

#
# config
#

config = misc.load_config ('.speechrc')
speech_arc     = config.get("speech", "speech_arc")
speech_corpora = config.get("speech", "speech_corpora")

#
# convert mp3 to wav, in speaker directories
#

misc.mkdirs('%s/speechcommands' % (speech_corpora,))

words = [
    'backward', 'bed', 'bird', 'cat', 'dog', 'down', 'eight', 'five', 'follow', 'forward',
    'four', 'go', 'happy', 'house', 'learn', 'left', 'marvin', 'nine', 'no', 'off',
    'on', 'one', 'right', 'seven', 'sheila', 'six', 'stop', 'three', 'tree', 'two',
    'up', 'visual', 'wow', 'yes', 'zero',
]

with open('%s/speech_commands_v0.02/testing_list.txt' % speech_arc, 'r') as testing_listf:
    test_paths = set(line.strip() for line in testing_listf)

cnt = 0
spk_ids = set()
with open('tmp/run_parallel.sh', 'w') as scriptf, \
        open('%s/speechcommands/utt_test.txt' % speech_corpora, 'w') as utt_testf:
    for word in words:
        for filepath in glob.glob(os.path.join(speech_arc, 'speech_commands_v0.02', word, '*.wav')):
            text = word
            match = re.match(r'(\w+)_nohash_(\d+).wav', os.path.basename(filepath))
            spk_id = match.group(1)
            utt_id = spk_id + '-' + word + '-' + match.group(2)

            if (word + '/' + match.group(0)) in test_paths:
                utt_testf.write('%s-v1_%s\n' % (spk_id, utt_id))

            if spk_id not in spk_ids:
                misc.mkdirs('%s/speechcommands/%s-v1/etc' % (speech_corpora, spk_id))
                misc.mkdirs('%s/speechcommands/%s-v1/wav' % (speech_corpora, spk_id))
                spk_ids.add(spk_id)

            with codecs.open ('%s/speechcommands/%s-v1/etc/prompts-original' % (speech_corpora, spk_id), 'a', 'utf8') as promptsf:
                promptsf.write('%s %s\n' % (utt_id, text))

            wavfn = '%s/speechcommands/%s-v1/wav/%s.wav' % (speech_corpora, spk_id, utt_id)
            cmd = 'ffmpeg -i %s %s' % (filepath, wavfn)
            print cnt, wavfn
            scriptf.write('echo %6d %s &\n' % (cnt, wavfn))
            scriptf.write('%s &\n' % cmd)

            cnt += 1
            if (cnt % options.num_cpus) == 0:
                scriptf.write('wait\n')

cmd = "bash tmp/run_parallel.sh"
print cmd
# os.system(cmd)
