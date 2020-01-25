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
# convert mozilla common speech to voxforge-style packages
#

import sys
import os
import codecs
import traceback
import logging
import csv

from optparse               import OptionParser
from nltools                import misc

PROC_TITLE        = 'moz_cv3_to_vf'
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

cnt = 0
spk_ids = set()
with open('tmp/run_parallel.sh', 'w') as scriptf:
    files = ['dev.tsv', 'other.tsv', 'test.tsv', 'train.tsv', 'validated.tsv',]:  # not 'invalidated.tsv'
    for tsvfn in files:
        with codecs.open('%s/cv_corpus_v3/%s' % (speech_arc, tsvfn), 'r', 'utf8') as tsvf:
            reader = csv.DictReader(tsvf, dialect='excel-tab')

            # client_id path sentence up_votes down_votes age gender accent
            for row in reader:
                # print row
                filename = row['path']
                text = row['sentence']
                spk_id = row['client_id']
                gender = 'f' if row['gender'] == 'female' else 'm'
                utt_id = os.path.splitext(filename)[0]
                filepath = os.path.join(speech_arc, 'cv_corpus_v3', 'clips', filename)

                if not os.path.isfile(filepath) or os.path.getsize(filepath) == 0:
                    continue

                if spk_id not in spk_ids:
                    misc.mkdirs('%s/cv_corpus_v3/%s-v1/etc' % (speech_corpora, spk_id))
                    misc.mkdirs('%s/cv_corpus_v3/%s-v1/wav' % (speech_corpora, spk_id))
                    # with open ('spk2gender.txt', 'a') as genderf:
                    #     genderf.write('%s %s\n' % (spk_id, gender))
                    spk_ids.add(spk_id)

                with codecs.open ('%s/cv_corpus_v3/%s-v1/etc/prompts-original' % (speech_corpora, spk_id), 'a', 'utf8') as promptsf:
                    promptsf.write('%s %s\n' % (utt_id, text))

                wavfn = '%s/cv_corpus_v3/%s-v1/wav/%s.wav' % (speech_corpora, spk_id, utt_id)
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
