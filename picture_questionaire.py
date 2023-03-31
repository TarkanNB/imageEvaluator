import streamlit as st
import random as rd
import csv
import os
from datetime import datetime


@st.cache_data
def get_all_picture_names_in_folder():
    #make a local file_log.txt.
    start_cmd = 'ls > file_log.txt'
    os.system(start_cmd)
    pictures = []
    #select only pictures from all available files in directory.
    with open('file_log.txt', 'r') as log:
        for name in log:
            if name.split(".")[-1] in ["jpg\n","jpeg\n","jfif\n","pjpeg\n","pjp\n","png\n","svg\n"]:
                pictures.append(name.split("\n")[0])
    #remove file_log.txt
    end_cmd = 'rm file_log.txt'
    os.system(end_cmd)
    if pictures:
        return pictures
    else:
        raise Exception("Error: could detect no picture files in local folder.")

def create_datasheet(images, dict_image_id, name=None):
    if not name:
        #create a name for datasheet if none given
        time = datetime.now()
        name = "plaque_identification_of_brain_tissues_" + time.strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
    with open(name, 'w', newline='') as datasheet:
        sheet = csv.writer(datasheet, dialect='unix')
        sheet.writerow(["image_name", "identification"])
        for image in images:
            sheet.writerow([image, dict_image_id[image]])

@st.cache_data
def datasheet_to_dictionary():
    image_to_id = dict()
    with open('plaque_evaluation.csv', newline='') as csvfile:
        plaque_identifications = csv.reader(csvfile, delimiter=' ', quotechar='|')
        for row in plaque_identifications:
            image_to_id[row[0]] = row[1]
    return image_to_id

### --- initialization of session --- ###
if 'image_to_id_dictionary' not in st.session_state:
    st.session_state.image_to_id_dictionary = dict()

all_pictures = get_all_picture_names_in_folder()
if 'picture_seq' not in st.session_state:
    #randomize the picture order
    st.session_state.picture_seq = rd.sample(all_pictures, len(all_pictures))
    st.session_state.number_of_pictures = len(st.session_state.picture_seq)

### --- Web page --- ###
if len(st.session_state.picture_seq) > 0:
    # identification ongoing #
    st.title("Identify the Brain tissue")
    
    ###picture, identification = st.columns(2)
    
    with st.sidebar:
        chosen_id = st.radio(
            "Identification options:",
            ("plaque", "could be a plaque", "not a plaque", "pass"))
        if chosen_id == "pass":
            st.write("skip this image?")
            next_picture_button = st.button("Next image")
        else:
            st.write(f"identified brain tissue image as {chosen_id}")
            next_picture_button = st.button("Next image")
        if next_picture_button:
            st.session_state.image_to_id_dictionary[st.session_state.picture_seq[-1]] = chosen_id
            st.session_state.current_picture = st.session_state.picture_seq.pop()
    with st.container():
    	picture = st.image(st.session_state.picture_seq[-1])
    	progress = st.session_state.number_of_pictures - len(st.session_state.picture_seq) + 1
    	st.write(f"image {progress} of {st.session_state.number_of_pictures} images.")
    
else:
    # finished with identification #
    st.title("All Brain tissues have been identified")
    create_datasheet(all_pictures, st.session_state.image_to_id_dictionary)

### information for development.

''
''
''
'Only for development'
'Internal values:'
''
'picture_seq:'
st.write(str(st.session_state.picture_seq))
''
'number of pictures in this folder:'
st.write(str(st.session_state.number_of_pictures))
''
'dictionary'
st.write(str(st.session_state.image_to_id_dictionary))
