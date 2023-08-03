# wisper_diarization_with_sharepoint_integration
In this repository, we perform the diarization of audio extracted from SharePoint using stable_ts (https://github.com/jianfch/stable-ts/tree/main#visualizing-suppression), speechbrain/spkrec-ecapa-voxceleb's  pyannote model, and the pre-processing  audio suggested in approaches-to-diarisation(https://github.com/mirix/approaches-to-diarisation/tree/main)


# parts of the transcription code. 

# 1 first we import required libraris to audio processing, shareponit conection
# 2 define the parameters model to stable whisper
# 3 connect  to share pont
# 4 Extract files from share point al define path to save . txt file in one drive

# 5 preprocesing file
# 6 apply model with VAD 
# 7 Apply diarization
# 8 Save file in one drive
# 9 delete original audio file from one drive



