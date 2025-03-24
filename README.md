# touchAnalysisTool
"analysisPipeline.py" is a Python-built analysis tool for semi-automated coding of affective touch interactions. Requires video file and .CSV tracking data from DeepLabCut.

## Inputs and Outputs

### File inputs: 
After pressing "Open New Video," users are prompted to select two files from their library:
1. Video file for coding (.mp4)
2. Output file from DeepLabCut containing 2D-point estimations (.csv)

### Auto-save file outputs: 
As each frame is labeled, the following files will be automatically updated and stored in a folder matching the name and path of the video file (sans file extension):
1. startFrames.csv
2. endFrames.csv
3. fingers.csv
4. type.csv
5. locations.csv
If the user has previously began analyzing this video, this data will automatically be loaded back in so they do not lose progress.

### Analysis file outputs:
Once labeling and measuring are complete, data will automatically be saved in the following files: 
1. all.csv (contains count #, touch type, finger of delivery,	location of contact, velocity (mm/s),	displacement (mm),	contact duration (s),	start frame #, and	end frame # for **all labels**). 
2. stroke.csv (contains count #, finger of delivery,	location of contact, velocity (mm/s),	displacement (mm),	contact duration (s),	start frame #, and	end frame # for all recorded strokes.)
3. resting.csv (contains count #, finger of delivery,	location of contact, contact duration (s),	start frame #, and	end frame # for all recorded static touch interactions.)
4. noContact.csv (contains count #, duration (s),	start frame #, and	end frame # for all recorded periods of no contact.)
5. selfTouch.csv (contains count #, duration (s),	start frame #, and	end frame # for all recorded periods of self touch.)
6. other.csv (contains count #, touch type, finger of delivery,	location of contact, velocity (mm/s),	displacement (mm),	contact duration (s),	start frame #, and	end frame # for recorded instances labeled "other".)

## Instructions and definitions

### How to use this tool for semi-automated coding
Due to the uncontrolled nature of naturalistic affective touch, this tool requires manual input describing when and where contact takes place. This is then used to automatically produce estimates of velocity and displacement, thus "semi-automated" coding. 
- Step 0. **DeepLabCut**
Prior to using this tool, one must use [DeepLabCut]([url](https://deeplabcut.github.io/DeepLabCut/README.html)) (Mathis et al., 2016) to track the 2D coordinates of points of interest. This will output a .csv file containing the frame-by-frame x,y coordinates of each point, as well as the estimated tracking accuracy. In our case, we created a ResNet50 network to track the thumb, index, and middle fingers on each hand during mother-infant touch, and kept coordinates with an accuracy > 60%. No modification of this .csv file is required.
- Step 1. **File input**
After running the "analysisPipeline.py" file, select "Load New Video." This will open a file selection window to select the video you wish to code. Once selected, another window will prompt you for the DeepLabCut output .csv file. Additional video controls will appear once both files are selected. 
- Step 2. **Video controls**
Users have control over playback speed (bottom left dropdown) when the video is playing. Further navigation controls include dragging the progress bar (timestamp appears in Python output terminal), or frame-by-frame controls on the right of the progress bar. The "<<" and ">>" controls jump forward or backward 10 frames respectively; whereas "<" and ">" jumps only one frame. Clicking the "Most Recent" button returns the user to the most recently labeled frame.
- Step 3. **Manually labeling frames**
When you determine the onset of touch you wish to label (e.g., when a hand makes contact to stroke the arm), the contact is detailed using the three dropdown menus on the right side. The "Which Finger?" menu is automatically populated with the body parts listed in the DeepLabCut .csv file (e.g., index-right, thumb-left). If there touch using multiple fingers, we selected a representative finger to track, either based on the DLC tracking accuracy or visibility in the video. The "Type of touch" menu consists of stroking, static touch/resting of the hand, no contact, self touch, and other (these gestures are currently hard coded, but can be changed/expanded). "Location of touch" consists of head, torso, arms, and legs.
Once the frame of touch onset is displayed in video window and the contact is properly detailed in the dropdown menus, click "Label Start" to mark the start of contact. Next, locate the frame containing contact offset (when the hand is no longer touching) using the video navigation and click "Label End." If you realize you made a mistake selecting the proper frame or in detailing the touch with the dropdowns, the "Undo Label" button will erase the most recent frame details (click multiple times will erase multiple labels).
**NOTE:** Ensure you detail the interaction properly before labeling the **START** of contact, as editing the dropdowns before the end label does not change the recorded contact details.
- Step 3.5 **Auto save and returning to work**
There is an auto-save functionality coded in to this tool. After labeling the first interaction, a folder matching the name of the video is created at the same file location (see the "Auto-save file output" section above). **Do not move the video or folder location, as the path is referenced when re-opening and you will have to start over.** These files are updated each time a frame is labeled. If you cannot complete the video in one session; you may close out of the interface at any time.
When returning, simply click the same video and DeepLabCut data file as you did when creating the project, and all prior labels will be loaded. Clicking the "Most Recent" button will navigate to the most recently labeled frame. 
- Step 4. **Estimating absolute measurements using pixel-based video data** 
To convert from pixel-based measurements to relevant, absolute units; we utilize the average measurements of different physiological locations provided in "The Measure of Man and Woman" (Tilley 1993). We typically use the grip width or dimensions of the finger.
Once all instances of contact are labeled in the video, navigate through the video until you find a frame clearly showing a known physiological reference point that appears in plane with the contact delivery. Clicking the "Measure" button opens a new window with an expanded view of the current frame. In this window, draw a straight line across the physiolocial reference measurement by selecting the start point (left click) and end point (right click). Hit any key and input the known measurement in millimeters.
- Step 5. **Automated analysis**
Once all frames are labeled and you have input a known measurement conversion, click the "Analyze" button. This will produce six output files in a folder matching the name of the video - one for each touch type as well as an "all.csv" containing every labeled interaction. See "Analysis output files" above for more details. 

### Contact definitions
