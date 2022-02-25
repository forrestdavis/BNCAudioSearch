import requests
from collections import namedtuple
import textgrid
import re

from BNCClasses import Transcript, Tape, Chunk, Utterance, transcripts2csv

from bs4 import BeautifulSoup

FileSet = namedtuple("FileSet", "textgrid, wav, html")


def get_transcripts(htmls):
    """Returns instances of Transcript organized in a dictionary for
    quick search by html.

    For example, for the link http://bnc.phon.ox.ac.uk/transcripts-html/D90.html

    The link points to an instance of Transcript, which records 
    the speaker info at the top of the html (10 speakers e.g., D90PS000). 
    There is only one Tape, which encodes the units of speech by 
    one speaker. The first unit is spoken by D90PS000 which contains 
    8 utterances (e.g., the 8th is "So Brenda"). 

    Returns: 
        Dict[Transcript]: Dict index by html of transcript information. 
                            Transcipt corresponds to all the info from 
                            html which is composed of instances of Tapes
                            which groups transcripts into tape groupings 
                            which map onto TextGrids. Each Tape 
                            has a list of instances of Chunk, which is 
                            a group of speech acts (utterances) by 
                            one speaker. The goal is to faithfully 
                            encode the information from the html 
                            link, so look there for clarification 
                            at the natural groupings. 
    """

    transcripts = {}

    for html in htmls:

        print(f"Loading {html}...")
        #if html != 'http://bnc.phon.ox.ac.uk/transcripts-html/HYG.html':
        #    continue
        
        transcript = Transcript(html)
        transcripts[html] = transcript

        #Load html
        soup = BeautifulSoup(requests.get(html).content, "html.parser")

        tables = soup.findAll("table")
        headings = [heading.get_text(strip=True) for heading in soup.findAll("h4")]

        hasSpeakerInfo = 1
        if 'speaker' not in headings[0] and 'recorded' not in headings[0]:
            hasSpeakerInfo = 0

        speakers = {}

        if hasSpeakerInfo:
            #Get info from speaker table
            speaker_table = tables[0]
            for row in speaker_table.findAll("tr"):
                cells = [cell.get_text(strip=True).replace('\n', '') for cell in row.findAll('td')]
                speaker = cells[0].split(' ')[0]
                ageCat = cells[1]
                gender = cells[2]
                extra = cells[3]
                age = extra.split(',')[1].split(')')[0].replace('age', '').strip()

                speakers[speaker] = {'ageCat': ageCat, 'gender': gender, 'age': age, 'extra': extra}
            #Dialogues are 3rd table onward
            dialogues = tables[1:]
            tapes = headings[2:]

        #No speaker info (e.g., http://bnc.phon.ox.ac.uk/transcripts-html/HYG.html)
        else:
            dialogues = tables
            tapes = headings[1:]

        #add transcript speaker info
        transcript.speakers = speakers

        #Ensure everything is good
        assert len(tapes) == len(dialogues), 'Mismatch in tape titles and dialogues'

        re_decimal = re.compile('[0-9_]+')

        for tape, dialogue in zip(tapes, dialogues):
            TAPE = Tape(tape)
            transcript.tapes.append(TAPE)

            for row in dialogue.findAll("tr"):
                nums = []
                utterances = []

                cells = [cell.get_text() for cell in row.findAll('td')]

                #Sanity check
                assert len(cells) == 2, "More cells than expected for speech act"

                speaker = cells[0].strip().split('(')[-1].replace(')', '').strip()
                speech_acts = cells[1].strip().split('\n')
                for speech_act in speech_acts:
                    speech_act = speech_act.strip().split(' ')
                    num = speech_act[0].replace('[', '').replace(']', '')

                    #Get rid of empty spaces
                    words = []
                    for word in speech_act[1:]:
                        word = word.strip()
                        if word != '':
                            words.append(word)
                    utterance = ' '.join(words)

                    if re.match(re_decimal, num) is None:
                        continue

                    nums.append(num)
                    utter = Utterance(utterance)
                    utterances.append(utter)

                chunk = Chunk(speaker, nums, utterances)
                TAPE.chunks.append(chunk)
    return transcripts

def align_text_transcriptions(utter, words):
    """Returns tuples aligning words in utter (string 
    from transcript) with words in TextGrid (textgrid 
    object) 

    Returns: 
        List[Tuple]: List of tuples with words in transcript text 
                    aligned with transcribed words. Throws an 
                    AssertationError if alignment fails.
    """

    re_dots = re.compile('[\.]{2,6}')
    re_brackets = re.compile("\[[a-z\s*\'\+A-Z]*\]")
    re_dates = re.compile('[0-9]+th')

    utter = utter.replace('/', ' ').replace('-', ' ')
    utter = utter.replace(' & ', ' and')
    utter = re.sub(re_brackets, '', utter)

    ###Bunch of random issues
    utter = utter.replace('—', '')
    #I could parse this issue away...
    utter = utter.replace(" 's", "'s")
    utter = utter.replace(" n't", "n't")
    utter = utter.replace(" 'll", "'ll")
    utter = utter.replace("]'s", "] 's")
    utter = utter.replace(" 'un", "'un")
    utter = utter.replace("an' ", "an'")
    utter = utter.replace("o' ", "o'")
    utter = utter.replace("o 'clock", "o'clock")
    utter = utter.replace("Now,Mond", "Now, Mond")
    utter = utter.replace(".ep", "")
    utter = utter.replace("oiA_011207.tmp", 'oiA_011207 .tmp')
    utter = utter.replace("smelly's", "smelly 's")
    utter = utter.replace("0's", "0 's")
    utter = utter.replace("&;", "")
    #fix comma without space
    utter = re.sub(r"(?<=[,])(?=[^\s])", r" ", utter)

    #word in utterance text X list of transcribed words
    utter_words = []

    for text_word in utter.split(' '):
        text_word = text_word.strip()
        #String trailing punctuation
        plain_word = text_word.translate(str.maketrans('', '', ",.;:?!)(")).lower()

        if text_word == '' or plain_word == '' or text_word == "'":# or plain_word.isnumeric():
            continue

        assert len(words) != 0
        grid_word = words.pop(0)

        #Weird coding issue with ed.2 in http://bnc.phon.ox.ac.uk/transcripts-html/KDP.html
        if plain_word == 'ed2':
            plain_word = 'ed'

        if plain_word[-1] == "'":
            plain_word = plain_word[:-1]

        grid_text = grid_word.mark.lower()
        grid_words = [grid_word]

        #print(f"utterance {utter} text word {text_word} plain word {plain_word} grid word {grid_word.mark.lower()}")
        counter = 0
        #elif plain_word[1:] == grid_text:
        #    plain_word = grid_text
        while grid_text != plain_word:

            if grid_text == '{oov}':
                plain_word = grid_text
            elif plain_word.replace("'", '') == grid_text:
                plain_word = grid_text
            elif grid_text.replace("'", '') == plain_word:
                plain_word = grid_text
            elif plain_word.replace("'", '') == grid_text.replace("'", ''):
                plain_word = grid_text

            elif (grid_text in {'{gap_anonymization}', '{lg}', 
                    '{xx}', '{gap_anonymization_name}', '{cg}', '{br}', 
                    '{gap_name}', '{gap_address}', 
                    '{gap_anonymization_address}', 
                    '{gap_anonymization_telephonenumber}'}):
                assert len(words) != 0
                grid_word = words.pop(0)
                grid_text = grid_word.mark.lower()
            else:
                grid_words = [grid_word]
                assert len(words) != 0
                new_grid_word = words.pop(0)
                grid_words.append(new_grid_word)
                new_text = new_grid_word.mark.lower()
                if new_text in {'{gap_anonymization}', 
                '{gap_anonymization_name}', '{gap_name}',
                '{gap_anonymization_address}', '{lg}'}:
                    new_text = ''
                grid_text += new_text
                #Weird coding issue with d'you
                if grid_text == 'dyou':
                    grid_text = "d'you"
                counter += 1
                #print('\t', grid_text)
                assert counter < 5

        assert plain_word == grid_text
        utter_words.append((text_word, grid_words))

    return utter_words


def get_aligned_utterances(files, transcripts, 
        textgrid_path='data/AudioBNCTextGrids/'):
    """Returns updated instances of Transcript, with 
    word and phone level transcriptions aligned, 
    organized in a dictionary for quick search by html.

    For example, for the link http://bnc.phon.ox.ac.uk/transcripts-html/D90.html

    The link points to an instance of Transcript, which records 
    the speaker info at the top of the html (10 speakers e.g., D90PS000). 
    There is only one Tape, which encodes the units of speech by 
    one speaker. The first unit is spoken by D90PS000 which contains 
    8 utterances (e.g., the 8th is "So Brenda"). These utterances 
    are mapped to BNCClasses Utterance object with contains 
    the words, phones, and start/end times. To save memory, 
    other details (e.g., word alignments, were removed). 
    Running clip.py will align words with clipped audio, however.

    Note: This catches assertation errors from get_aligned_utterances 
            and errors from loading TextGrids with textgrid. The former 
            is recorded in alignment_issues.txt, and the later 
            is recorded in errorful_textgrids.txt.

    Returns: 
        Dict[Transcript]: Dict index by html of transcript information. 
                            Transcipt corresponds to all the info from 
                            html which is composed of instances of Tapes
                            which groups transcripts into tape groupings 
                            which map onto TextGrids. Each Tape 
                            has a list of instances of Chunk, which is 
                            a group of speech acts (utterances) by 
                            one speaker. These utterances 
                            are further aligned with transcriptions. 
                            The goal is to faithfully 
                            encode the information from the html 
                            link, so look there for clarification 
                            at the natural groupings. 
    """

    errors = open('errorful_textgrids.txt', 'w')
    alignment_issues = open('alignment_issues.txt', 'w')

    for f in files:
        if f.html not in transcripts:
            continue

        print(f"aligning {f.textgrid}...")

        transcript = transcripts[f.html]
        tape_num = int(f.textgrid.split('.TextGrid')[0].split('_')[-1])
        tape = transcript.tapes[tape_num-1]

        textgrid_fname = textgrid_path+f.textgrid.split('/')[-1]
        try:
            tg = textgrid.TextGrid.fromFile(textgrid_fname)
        except:
            errors.write(f.textgrid+'\n')
            tg = None

        if tg is None:
            continue

        phones, words = tg[0], tg[1]
        #safety check
        assert tg[0].name == 'phone' and tg[1].name == 'word'

        #Filter out pauses and make
        #list of intervals
        words = list(filter(lambda x: not (x.mark == 'sp'), words))#or x.mark[0] == '{'), words))
        for chunk in tape:
            for utterance in chunk:
                utter = utterance.text
                utterance.set_fnames(f)
                try:
                    utter_words = align_text_transcriptions(utter, words)
                except AssertionError:
                    alignment_issues.write(f"utterance {utter} textgrid: {f.textgrid} html: {f.html}\n")
                    continue

                for idx, w in enumerate(utter_words):
                    w_text, intervals = w
                    w_original = w_text
                    w_text = w_text.translate(str.maketrans('','', ",.;:?!)(")).lower()
                    #utterance.words.append(w_text)
                    utterance.words += ' ' +w_text

                    w_start = intervals[0].minTime
                    w_end = intervals[-1].maxTime
                    if idx == 0:
                        utterance.start = w_start
                    start_idx = phones.indexContaining(w_start)+1
                    end_idx = phones.indexContaining(w_end)+1
                    phones_str = []
                    for p in phones[start_idx:end_idx]:
                        phones_str.append(p.mark)
                    phones_str = ' '.join(phones_str)
                    #utterance.phones.append(phones_str)
                    utterance.phones += phones_str + ' | '

                utterance.end = w_end
                chunk.transcribed_utterances.append(utterance)

    errors.close()
    alignment_issues.close()
    return transcripts

def get_utterances(path='data/'):
    """Returns instances of Transcript, with 
    word and phone level transcriptions aligned, 
    organized in a dictionary for quick search by html.

    For example, for the link http://bnc.phon.ox.ac.uk/transcripts-html/D90.html

    The link points to an instance of Transcript, which records 
    the speaker info at the top of the html (10 speakers e.g., D90PS000). 
    There is only one Tape, which encodes the units of speech by 
    one speaker. The first unit is spoken by D90PS000 which contains 
    8 utterances (e.g., the 8th is "So Brenda"). These utterances 
    are mapped to BNCClasses Utterance objects. 

    Returns: 
        Dict[Transcript]: Dict index by html of transcript information. 
                            Transcipt corresponds to all the info from 
                            html which is composed of instances of Tapes
                            which groups transcripts into tape groupings 
                            which map onto TextGrids. Each Tape 
                            has a list of instances of Chunk, which is 
                            a group of speech acts (utterances) by 
                            one speaker. These utterances 
                            are further aligned with transcriptions. 
                            The goal is to faithfully 
                            encode the information from the html 
                            link, so look there for clarification 
                            at the natural groupings. 
    """

    import dill
    from os.path import exists

    ###List of FileSet (namedtuple with attrs textgrid, wav, html)
    ### and list of htmls
    files, htmls = get_aligned_fnames(path)
    htmls.sort()

    ##Load in transcript information
    transcripts_fname = 'data/transcripts.pkl'
    if exists(transcripts_fname):
        print(f"Loading {transcripts_fname}...")
        with open(transcripts_fname, 'rb') as f:
            transcripts = dill.load(f)
    else:
        transcripts = get_transcripts(htmls)
        print(f"Saving {transcripts_fname}...")
        with open(transcripts_fname, 'wb') as f:
            dill.dump(transcripts, f)

    ##Align transcript utterances with TextGrids and audio
    aligned_transcripts_fname = 'data/aligned_transcripts.pkl'
    if exists(aligned_transcripts_fname):
        print(f"Loading {aligned_transcripts_fname}...")
        with open(aligned_transcripts_fname, 'rb') as f:
            transcripts = dill.load(f)
    else:
        transcripts = get_aligned_utterances(files, transcripts)
        print(f"Saving {aligned_transcripts_fname}...")
        with open(aligned_transcripts_fname, 'wb') as f:
            dill.dump(transcripts, f)

    return transcripts

def get_aligned_fnames(path='data/'):
    """Returns textgrids with wav and html 
    files. 

    Returns: 
        List[FileSet], List[str]: List of namedtuples for each textgrid file, 
                        associating with each textgrid it's wav 
                        file and it's html transcript. Also 
                        return list that is subset of html transcript
                        links which are trancscribed phonetically.
    """

    ##Get all transcript links
    with open(path+'filelist-html.txt', 'r') as f:
        URLS = list(map(lambda x: x.strip(), f.readlines()))
        URLS_set = set(URLS)
    ###Get all textgrid fnames
    with open(path+'filelist-textgrid.txt', 'r') as f:
        textgrids = list(map(lambda x: x.strip(), f.readlines()))
    ###Get all wav fnames
    with open(path+'filelist-wav.txt', 'r') as f:
        wavs = list(map(lambda x: x.strip(), f.readlines()))
        wav_set = set(wavs)

    html_base_url = 'http://bnc.phon.ox.ac.uk/transcripts-html/'
    files = []
    used_html = set([])
    for textgrid in textgrids:
        info = textgrid.split('.TextGrid')[0].split('_')
        wav_url, tape, html, _ = info

        wav_url += '.wav'
        #check we have wav file
        assert wav_url in wav_set, f"Missing WAV: {wav_url}"

        html_url = html_base_url+html+'.html'
        #check we have html url
        assert html_url in URLS_set, f"Missing HTML: {html_url}"
        used_html.add(html_url)

        files.append(FileSet(textgrid, wav_url, html_url))

    return files, list(used_html)

if __name__ == "__main__":

    transcripts = get_utterances()

    transcripts2csv(transcripts, 'BNCAudio_utterances.tsv')
