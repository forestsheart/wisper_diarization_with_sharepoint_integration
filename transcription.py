#We define utf-8.
import locale
def getpreferredencoding(do_setlocale = True):
    return "UTF-8"
locale.getpreferredencoding = getpreferredencoding

import libraries
#importamos libreria


import datetime #
import subprocess #modificar archivos junto a ff

#manejo audio
from pyannote.audio import Audio
from pyannote.core import Segment

import wave

import numpy as np
#cluster to diarization
from sklearn.cluster import AgglomerativeClustering #clasificación
import stable_whisper
import wave##
import torch  gpu
import pyannote.audio #manejo de audio
from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding #modelo pre-enmtrenado
embedding_model = PretrainedSpeakerEmbedding(
    "speechbrain/spkrec-ecapa-voxceleb",
    device=torch.device("cuda")) #modelo pre entrenado para diarización

# share-point
import contextlib
from office365.runtime.auth.authentication_context import AuthenticationContext #Conexión a sharepoint
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File


#miselanius
from functools import reduce
from pydub import AudioSegment, effects
import tempfile
import os



#we define the model
#definimos parametros del modelo
num_speakers = 2 #@param {type:"integer"}

language = 'Spanish' #@param ['any', 'English','Spanish']

model_size = 'large-v2' #@param ['tiny', 'base', 'small', 'medium', 'large','large-v2']


model_name = model_size
if language == 'Spanish' and model_size != 'base':
  model_name += '.es'


#get the model
model = stable_whisper.load_model(model_size
                                  )

#connect to share point path audio files
site_url = "https://your_site/personal/your_username/"
folder_path="/personal/your_username/path_to_your_from_folder..."
folder_path_audios="/personal/your_username/path_to_your_transcripted_files_folder..."
username = "your_user_name"
password = "your_password"

ctx_auth = AuthenticationContext(site_url)
if ctx_auth.acquire_token_for_user(username, password):
    ctx = ClientContext(site_url, ctx_auth)
else:
    print("Error de autenticación")


#set folder audio files
root_folder = ctx.web.get_folder_by_server_relative_url(folder_path)
#set folder to save texts files
root_folder_txt=ctx.web.get_folder_by_server_relative_url(folder_path_audios)
ctx.load(root_folder, ["Files"]) #get files
ctx.execute_query()
#get transcriptiont to each files
for i in range(0, len(root_folder.files)):
    file_url = '/personal/your_username/path_to_your_from_folder...'+root_folder.files[i].name
    source_file = ctx.web.get_file_by_server_relative_url(file_url)#jalo archivo

    local_file_name = os.path.join('/content/', os.path.basename(file_url))#define the path to save the file
    with open(local_file_name, "wb") as local_file:
        path = local_file_name
        source_file.download(local_file).execute_query()#download the file
        print("[Ok] file has been downloaded: {0}".format(path))
       
       
#pre-procesing mp3 files
        if path[-3:] == 'mp3':
            subprocess.call(['ffmpeg', '-i', path, path[:-3]+'wav', '-y'])
            path = path[:-3]+'wav'
            os.remove(local_file_name) #remove original audio
            rawsound = AudioSegment.from_file(path, 'wav')
            rawsound = rawsound.set_channels(1)
            rawsound = rawsound.set_frame_rate(16000)
            normalizedsound = effects.normalize(rawsound)
            normalizedsound.export(path, format='wav')
            #model with vad silence detecction to improve large-v2 model and regrouping
            result = model.transcribe(path,language="es",regroup='sp=.* /。/?/？/．/!/！',
                                  vad=True#
                                  
                                  )  # aplicamos whisper
            segments = result.to_dict()["segments"]#result["segments"]  # extract segments
            #diarization 
            with contextlib.closing(wave.open(path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
                audio = Audio()

            def segment_embedding(segment):
                start = segment["start"]
                # Whisper overshoots the end timestamp in the last segment
                end = min(duration, segment["end"])
                clip = Segment(start, end)
                waveform, sample_rate = audio.crop(path, clip)
                return embedding_model(waveform[None])

            embeddings = np.zeros(shape=(len(segments), 192))
            for i, segment in enumerate(segments):
                embeddings[i] = segment_embedding(segment)

            embeddings = np.nan_to_num(embeddings)
            clustering = AgglomerativeClustering(num_speakers).fit(embeddings)
            labels = clustering.labels_
            for i in range(len(segments)):
                segments[i]["speaker"] = 'SPEAKER ' + str(labels[i] + 1)

            def time(secs):
                return datetime.timedelta(seconds=round(secs))
#save local  .txt file in colab 
            f = open(path[:-4]+".txt", "w", encoding="utf-8")
            for (i, segment) in enumerate(segments):
                if i == 0 or segments[i - 1]["speaker"] != segment["speaker"]:
                    f.write("\n" + segment["speaker"] + ' ' + str(time(segment["start"])) + '\n')
                f.write(segment["text"][1:] + ' ')
            f.close()
            print("[Ok] file has been transcripted: {0}".format(path))
#save file in one drive
            with open(path[:-4]+".txt", 'rb') as f:
                 file = root_folder_txt.files.upload(f).execute_query()
            print("File has been uploaded into: {0}".format(file.serverRelativeUrl))
            os.remove(path)#remove file 
            file = ctx.web.get_file_by_server_relative_url(file_url)
            file.delete_object().execute_query()#delete original file from one drive
            print("[Ok] file has been deleted from one drive: {0}".format(path))

