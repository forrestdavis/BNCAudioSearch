
# BNCAudioSearch

The following is a tool kit designed to demonstrate 
searching for words in the BNC Audio corpus. It is for a course 
presentation, and so it has not been fully validated. Suggested additions 
are appreciated, but I may not have time to either implement them or 
check pull requests. 

## 0. What you need 

Complete the Registration for BNC at the bottom of the web page ([link](http://www.phon.ox.ac.uk/AudioBNC))  

Download [Praat](https://www.fon.hum.uva.nl/praat/)

Install [textgrid](https://github.com/kylebgorman/textgrid)

## 1. Get Data

Make a directory called data and add the following files.

Download the list of filenames 

- wav files ([link](http://bnc.phon.ox.ac.uk/filelist-wav.txt))
- html files ([link](http://bnc.phon.ox.ac.uk/filelist-html.txt)) 
- TextGrid files ([link](http://bnc.phon.ox.ac.uk/filelist-textgrid.txt))

Download the Praat TextGrids and extract files

- [link](https://reshare.ukdataservice.ac.uk/851496/)

For reference, the phone symbols used in the TextGrids

- [link](http://www.phon.ox.ac.uk/files/docs/BNC_transcription_alphabet.html)

For reference, html versions of the orthographically transcribed speech (i.e. the words in spelling)

- [link](http://bnc.phon.ox.ac.uk/transcripts-html/)


## 2. Aligning words (orthography) with wav files and TextGrids

You can skip to 3 if you already have the necessary tsv file and want to just look 
for words.  

If you'd like to recreate the tsv file, run:

```
python align.py 
```

This will create a binary files transcripts.pkl and aligned\_transcripts.pkl in the data dir that stores the aligned 
transcripts and transcriptions. This will then save a tsv file (BNCAudio\_utterances.tsv).

## 3. Searching for words (orthographic)

Searching with Praat given the alignments is not familiar to me; see [BNC demo](http://www.phon.ox.ac.uk/jcoleman/PraatSearch.html)

Instead, align.py creates a tsv file which can faciliate searching. It is grouped at the utterance level, so each row is an utterance. The headings and their meanings are below:

```
tape: name of tape
speaker: speaker identifier
gender: gender of speaker (m|f|u)
age: age of speaker (0-100|unknown)
tape utterance num: utterance number in tape (e.g., 5th utterance)
speaker utterance num: utterance number for speaker in turn (e.g., 2nd uninterrupted utterance)
transcript num: transcript number utterance is from
utterance text: utterance in orthography with any punctuation
cleaned text: utterance in orthography without any puncutation
phones: phones in utterance or word, words boundary is marked with |
start time: start time in audio of utterance or word
end time: end time in audio of utterance or word 
wav fname: wav filename
TextGrid fname: TextGrid file name
transcript html: HTML link of orthographic transcript
link: Link for downloading word or utterance
padded link: Link for downloading word or utterance with 30 second buffer on either side
python clip command: Script command to get wav and TextGrid for just utterance or word
python padded clip command: Like above but with paddding
```

So for example, say you want to find the word gronnies, as per BNC's website:

1. Open BNCAudio\_utterances.tsv
2. Navigate to utterance text column
3. Search for gronnies
4. copy the cell under the link column and paste in browswer (this will download the 
wav file)

Alernatively, if you'd like the wav and TextGrid aligned for the utterance containing 
gronnies, after 3 above

1. Copy the cell under the 'python clip command' column. 
2. Run this from command line and a wav file and an aligned TextGrid will be save under data/downloads

You should see something like the following if you open the wav and TextGrid in Praat:


![gronnies](figures/gronnies.png)

## 4. Searching for phonemes

Suppose you want to find man ending compounds with secondary stress. First consulate the 
phoneme to character [mappings](http://www.phon.ox.ac.uk/files/docs/BNC_transcription_alphabet.html). To simplify say, we want to find [m ae n]# with ae bearing secondary stress.

1. Open BNCAudio\_utterances.tsv
2. Search for M AE2 N |
3. Copy relevant links

For example, handyman can be found in the utterance [here](http://bnc.phon.ox.ac.uk/data/021A-C0897X0905XX-AAZZP0-2nd-ABZZP0.wav?t=4541.4925,4544.1125). You can clip the audio and align 
the TextGrid using 

```
python clip.py --start 4541.4925 --end 4544.1125 --textgrid_fname 021A-C0897X0905XX-AAZZP0-2nd-ABZZP0_090501_H49_1.TextGrid --out_fname 021A-C0897X0905XX-AAZZP0-2nd-ABZZP0_090501_H49_1_4541.4925_4544.1125 --getwav
```

Now open the wav and TextGrid files under downloads in Praat. You should see:

![handyman](figures/handyman.png)

## Notes
- There are some outstanding alignment issues and some issues with loading a small subset 
        of the textgrids (see alignment_issues.txt and errorful_textgrids.txt for 
        the relevant files)
- align could be made considerably faster if aligning textgrids with orthographic transcriptions was done when initially saving the transcripts. In development it was easier to break these steps into two separate loops. 