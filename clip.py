import textgrid
import requests
import pathlib
import argparse

parser = argparse.ArgumentParser(description='Clipping Audio and TextGrids from BNC Audio')

parser.add_argument('--start', type=float, 
                    help='start time')
parser.add_argument('--end', type=float, 
                    help='end time')
parser.add_argument('--padding', type=float, default=0.,
                    help='amount of padding time')
parser.add_argument('--textgrid_fname', type=str, 
                    help='TextGrid filename')
parser.add_argument('--out_fname', type=str, 
                    help='TextGrid (and wav) output filename')
parser.add_argument('--getwav', action='store_true',
                    help='Specify whether to get wav')

args = parser.parse_args()

#Code
outpath = 'data/downloads/'
if args.getwav:
    wav_path = 'http://bnc.phon.ox.ac.uk/data/'
    wavlink = wav_path+args.textgrid_fname.split('_')[0]+'.wav'+'?t='+str(max(args.start-args.padding, 0))+','+str(args.end+args.padding)
    r = requests.get(wavlink, allow_redirects=True)

    outwav_path = outpath+'audio/'
    pathlib.Path(outwav_path).mkdir(parents=True, exist_ok=True)
    with open(outwav_path+args.out_fname+'.wav', 'wb') as f:
        f.write(r.content)

path = 'data/AudioBNCTextGrids/'
tg = textgrid.TextGrid.fromFile(path+args.textgrid_fname)

phones = tg.getFirst('phone')
words = tg.getFirst('word')

phone_start_idx = phones.indexContaining(args.start)+1
phone_end_idx = phones.indexContaining(args.end)+1

word_start_idx = words.indexContaining(args.start)+1
word_end_idx = words.indexContaining(args.end)+1

target_phones = phones[phone_start_idx:phone_end_idx]
target_word = words[word_start_idx:word_end_idx]

args.start -= args.padding
args.end += args.padding

phone_tier = textgrid.IntervalTier(name='phone', maxTime=args.end-args.start)
word_tier = textgrid.IntervalTier(name='word', maxTime=args.end-args.start)

outGrid = textgrid.TextGrid(maxTime = args.end-args.start)
outGrid.append(phone_tier)
outGrid.append(word_tier)

for p in target_phones:
    p.__isub__(args.start)
    phone_tier.addInterval(p)

for w in target_word:
    w.__isub__(args.start)
    word_tier.addInterval(w)

outgrid_path = outpath+'textgrids/'
pathlib.Path(outgrid_path).mkdir(parents=True, exist_ok=True)
outGrid.write(outgrid_path+args.out_fname+'.TextGrid')
