# This script opens each sound file in a directory, looks for a corresponding TextGrid in (possibly) a different directory, and extracts f0, F1, F2, and Intensity from the midpoint(s) of any labelled interval(s) in the specified TextGrid tier.  It also extracts the duration of the labelled interval(s).  All these results are written to a tab-delimited text file.
# The script is a modified version of the script "collect_formant_data_from_files.praat" by Mietta Lennes, available here: http://www.helsinki.fi/~lennes/praat-scripts/
# The modifications were done by Dan McCloy (drmccloy@uw.edu) in December 2011.
#
# Additional modifications (addition of Intensity, 
# getting word and phone tier rather than asking for tier) 
# was done by Forrest Davis (fd252@cornell.edu) in February 2022.

# This script is distributed under the GNU General Public License.
# Copyright 4.7.2003 Mietta Lennes

form Get pitch formants intensity and duration from labeled segments in files
	comment Directory of sound files. Be sure to include the final "/"
	text sound_directory data/downloads/audio/
	sentence Sound_file_extension .wav
	comment Directory of TextGrid files. Be sure to include the final "/"
	text textGrid_directory data/downloads/textgrids/
	sentence TextGrid_file_extension .TextGrid
	comment Full path of the resulting text file:
	text resultsfile praat_measures.csv
	comment Formant analysis parameters
	positive Time_step 0.01
	integer Maximum_number_of_formants 5
	positive Maximum_formant_(Hz) 5500
	positive Window_length_(s) 0.025
	real Preemphasis_from_(Hz) 50
	comment Pitch analysis parameters
	positive Pitch_time_step 0.01
	positive Minimum_pitch_(Hz) 75
	positive Maximum_pitch_(Hz) 600
endform

#Set Tiers
phoneTier = 1
wordTier = 2

# Make a listing of all the sound files in a directory:
Create Strings as file list... list 'sound_directory$'*'sound_file_extension$'
numberOfFiles = Get number of strings

# Check if the result file exists:
if fileReadable (resultsfile$)
	pause The file 'resultsfile$' already exists! Do you want to overwrite it?
	filedelete 'resultsfile$'
endif

# Create a header row for the result file: (remember to edit this if you add or change the analyses!)
header$ = "fname,word,phone,start,end,midpoint,duration,f0_mid,intensity_mid,f0_max,f0_min,f0_mean,f0_std,intensity_max,intensity_min,intensity_mean,intensity_std,F1_mid,F2_mid'newline$'"
fileappend "'resultsfile$'" 'header$'

# Open each sound file in the directory:
for ifile to numberOfFiles
	filename$ = Get string... ifile
	Read from file... 'sound_directory$''filename$'

	# get the name of the sound object:
	soundname$ = selected$ ("Sound", 1)

	# Look for a TextGrid by the same name:
	gridfile$ = replace$ (filename$, sound_file_extension$, textGrid_file_extension$,1)
	gridfile$ = "'textGrid_directory$''gridfile$'"

	# if a TextGrid exists, open it and do the analysis:
	if fileReadable (gridfile$)
		Read from file... 'gridfile$'

		select Sound 'soundname$'
		To Formant (burg)... time_step maximum_number_of_formants maximum_formant window_length preemphasis_from

		select Sound 'soundname$'
		To Pitch... pitch_time_step minimum_pitch maximum_pitch

                select Sound 'soundname$'
                To Intensity... 100 0

		select TextGrid 'soundname$'
		numberOfIntervals = Get number of intervals... phoneTier

		# Pass through all intervals in the designated tier, and if they have a label, do the analysis:
		for interval to numberOfIntervals
			phone$ = Get label of interval... phoneTier interval
			if phone$ <> ""
				# duration:
				start = Get starting point... phoneTier interval
				end = Get end point... phoneTier interval
				duration = end-start
				midpoint = (start + end) / 2
                                
                                # get word:
                                wordNum = Get interval at time... wordTier midpoint
                                word$ = Get label of interval... wordTier wordNum

				# formants:
				select Formant 'soundname$'
				f1_mid = Get value at time... 1 midpoint Hertz Linear
				f2_mid = Get value at time... 2 midpoint Hertz Linear

				# pitch:
				select Pitch 'soundname$'
				f0_50 = Get value at time... midpoint Hertz Linear
                                pitchmax = Get maximum... start end Hertz Parabolic
                                pitchmin = Get minimum... start end Hertz Parabolic
                                pitchmean = Get mean... start end Hertz
                                pitchstd = Get standard deviation... start end Hertz

                                # intensity:
                                select Intensity 'soundname$'
                                intensity_mid = Get value at time... midpoint Cubic
                                intensity_max = Get maximum... start end Parabolic
                                intensity_min = Get minimum... start end Parabolic
                                intensity_mean = Get mean... start end dB
                                intensity_std = Get standard deviation... start end
				# Save result to text file:
				resultline$ = "'soundname$','word$','phone$','start','end','midpoint','duration','f0_50','intensity_mid','pitchmax','pitchmin','pitchmean','pitchstd','intensity_max','intensity_min','intensity_mean','intensity_std','f1_mid','f2_mid''newline$'"
				fileappend "'resultsfile$'" 'resultline$'

				# select the TextGrid so we can iterate to the next interval:
				select TextGrid 'soundname$'
			endif
		endfor
		# Remove the TextGrid, Formant, and Pitch objects
		select TextGrid 'soundname$'
		plus Formant 'soundname$'
		plus Pitch 'soundname$'
                plus Intensity 'soundname$'
		Remove
	endif
	# Remove the Sound object
	select Sound 'soundname$'
	Remove
	# and go on with the next sound file!
	select Strings list
endfor

# When everything is done, remove the list of sound file paths:
Remove

