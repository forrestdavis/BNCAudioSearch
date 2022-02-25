def transcripts2csv(transcripts, outname='temp.tsv'):

    print(f"Formatting transcripts to tsv")

    if type(transcripts) == dict:
        transcripts = list(transcripts.values())

    groupSize = 10

    utters_str = ''
    idx_start = 0
    for idx, transcript in enumerate(transcripts):

        utter_heading, utter_str = transcript.to_str('utterance', idx)
        if idx == 0:
            utters_str += utter_heading + '\n' + utter_str
        else:
            utters_str += utter_str

    print(f"Saving info to {outname}...")
    with open(outname, 'w') as o:
        o.write(utters_str)

class Transcript:

    def __init__(self, html):

        self.html = html
        self.speakers = {}
        self.tapes = []

    def __iter__(self):
        for tape in self.tapes:
            yield tape

    def to_str(self, level, transcript_num = 0, delim='\t'):

        heading = ['tape', 'speaker', 'gender', 'age', 
                'tape utterance num', 'speaker utterance num']
        entries = []
        if level == 'utterance':
            for tape in self.tapes:
                for chunk in tape:
                    chunk_num = 0
                    for utterance_num, utterance in chunk.get_transcribed():
                        chunk_num += 1
                        if chunk.speaker in self.speakers:
                            speaker_info = self.speakers[chunk.speaker]
                        else:
                            speaker_info = {}
                            speaker_info['gender'] = 'u'
                            speaker_info['age'] = 'unknown'
                        entry = [tape.text, chunk.speaker, speaker_info['gender'], 
                                speaker_info['age'], utterance_num, chunk_num]

                        entry_dict = utterance.get_entry_dict(transcript_num)
                        entry.extend(list(entry_dict.values()))
                        if len(heading) < len(entry):
                            heading.extend(list(entry_dict.keys()))

                        entries.append(delim.join(list(map(lambda x: str(x), entry))))

        heading = delim.join(heading)
        return heading, '\n'.join(entries)+'\n'

class Tape:

    def __init__(self, text): 
        self.text = text
        self.chunks = []

    def __iter__(self):
        for chunk in self.chunks:
            yield chunk

class Chunk:

    def __init__(self, speaker, nums, utterances):

        self.speaker = speaker
        self.nums = nums
        self.utterances = utterances
        self.transcribed_utterances = []

    def __iter__(self):
        for utterance in self.utterances:
            yield utterance

    def get_transcribed(self):
        for num, utter in zip(self.nums, self.transcribed_utterances):
            yield num, utter

class Utterance:

    def __init__(self, text):

        self.text = text
        self.start = 0
        self.end = 0
        self.words = ''
        self.phones = ''
        self.wavfname = ''
        self.textgridfname = ''
        self.transcriptlink = ''

    def __iter__(self):
        for word in self.words:
            yield word

    def set_fnames(self, f):
        self.textgridfname = f.textgrid.split('/')[-1]
        self.wavfname = f.wav.split('/')[-1]
        self.wavlink = f.wav
        self.transcriptlink = f.html

    def get_entry_dict(self, transcript_num, padding=30):


        clean_text = self.words.strip()

        #Some phonemes are lower case?? ae2 in D90_1.TextGrid
        phones_str = '| '+self.phones.strip().upper()

        link = self.wavlink+'?t='+str(self.start)+','+str(self.end)
        padded_link = self.wavlink+'?t='+str(max(self.start-padding, 0))+','+str(self.end+padding)
        UID = self.textgridfname.split('.TextGrid')[0]+'_'+str(self.start)+'_'+str(self.end)

        command = f"python clip.py --start {self.start} --end {self.end} --textgrid_fname {self.textgridfname} --out_fname {UID} --getwav"

        UID_pad = self.textgridfname.split('.TextGrid')[0]+'_'+str(self.start)+'_'+str(self.end)+'_pad'+str(padding)
        pad_command = f"python clip.py --start {self.start} --end {self.end} --textgrid_fname {self.textgridfname} --out_fname {UID_pad} --getwav --padding {padding}"


        entry_dict = {
                'transcript num': transcript_num,
                'utterance text': self.text, 
                'cleaned text': clean_text, 
                'phones': phones_str, 
                'start time': self.start, 
                'end time': self.end, 
                'wav fname': self.wavfname,
                'TextGrid fname': self.textgridfname,
                'tanscript html': self.transcriptlink,
                'link': link, 
                'padded link': padded_link, 
                'python clip command': command, 
                'python padded clip command': pad_command}

        return entry_dict
