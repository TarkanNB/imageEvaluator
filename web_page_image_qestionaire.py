""" This module takes images from the imgage directory,
    and shows them in a random order one by one on a webpage.
    Were it will prompt the evaluator for questions as given in the configuration.json file.
    It will store these responces in a datasheet after the last image has been shown. 
"""

from datetime import datetime
import os
import csv
import random as rd
from PIL import Image
import streamlit as st



class Picture:
    def __init__(self, sample_name, types, extension):
        self.sample = sample_name   # string
        self.types = types   # list of str
        self.full_name = dict()
        for t in types:
            self.full_name[t] = sample_name + "__" + t + "." + extension

    def all_variants(self):
        self.full_name.values()  # list of str

    def true_size(self):
        img = Image.open(self.full_name.values()[0])
        return img.size

    def show(self, the_type, scale=1):
        # rendes the image on the webpage with specified scale.
        path_to_image = "images/" + self.full_name[the_type]
        img = Image.open(path_to_image)
        if scale == 1:
            st.image(img, output_format='png')
        else:
            width, height = img.size
            image_size = (width * scale, height * scale)
            new_img = img.resize(image_size)
            st.image(new_img, output_format='png')

class Question:
    def __init__(self, key, database_name, type_of_question, question_discription, possible_answers=None):
        self.database_name = database_name
        self.type = type_of_question
        self.discription = question_discription
        self.options = possible_answers
        self.key = key
        self.evaluator_input = None

    def ask(self):
        if self.type == "text_input":
            return st.text_input(self.discription)
        elif self.type == "multiple_choice":
            return st.radio(self.discription, self.options)
        elif self.type == "selection_box":
            return st.selectbox(self.discription, self.options)


@st.cache_data
def get_the_path_to_main_directory():
    # Get the path to current directory on linux systems.
    start_cmd = "pwd > path.txt"
    os.system(start_cmd)
    with open("path.txt", 'r') as file:
        for line in file:
            path = line.split('\n')[0]
    end_cmd = "rm path.txt"
    os.system(end_cmd)
    return path

@st.cache_data
def get_all_picture(type_selection=None):
    # Get the list of images in the images directory
    images_log = os.listdir(get_the_path_to_main_directory() + '/images')

    pictures = []
    sample_name = ""
    types = []
    extension = ""
    for name in images_log:

        # Check for correct format, 
        # and extract sample type and extention names for image class.
        sample_typeextension = name.split("__")
        if len(sample_typeextension) != 2:
            raise Exception(f"Error: could not read {name}, " 
            + "image name has to have following form: {sample}___{type}.{extension} in the image folder")
        type_extension = sample_typeextension[1].split(".")
        if len(type_extension) != 2:
            raise Exception(f"Error: could not read {name}, "
            + "image name has to have following form: {sample}___{type}.{extension} in de image folder")
        extension = type_extension[1]
        if extension not in ["jpg", "jpeg", "jfif", "pjpeg", "pjp", "png", "svg"]:
            raise Exception(f"Error: uncleare extension in picture_folder: {extension} of file: {name}")

        # check if it is a new variation of sample or a new sample.
        if sample_name == sample_typeextension[0]:
            types.append(type_extension[0])
        elif types:
            pictures.append(Picture(sample_name, types, extension))
            sample_name = sample_typeextension[0]
            types = [type_extension[0]]
        else:
            sample_name = sample_typeextension[0]
            types = [type_extension[0]]

    if pictures:
        return pictures
    else:
        raise Exception("Error: could detect no picture files in local folder.")

@st.cache_data
def get_configurations():
    # [0]: fetches all conciguration veriables from the configuration.json file and stores it in a dictionary,
    # [1]: fetches all questions in configuration.json file and stores and stores them in a list of Questions(class).
    configurations = dict()
    questions = []
    question_variables = []
    key = 0  # unic key for each question.
    reading_input = False
    reading_question_input = False
    with open("configuration.json", "r") as conf_file:
        for line in conf_file:
            # checks if the line has to be ignored.
            if line[0] == "#" or line == "\n":
                continue
            # checks if a new variable needs to be declared.
            elif line[0:3] == ">>>":
                variable = line.split(">>>")[-1].split(":")[0]
                # start reading questions from the configuration file.
                if variable == "Questions":
                    reading_question_input = True
                # finished with the questions section of the configuration file.
                elif variable == "End_questions\n":
                    reading_question_input = False
                else:
                    reading_input = True  # start reading other variable from the file.
            elif reading_input:
                # bind value to declared variable
                configurations[variable] = line.split("$")[1]
                reading_input = False
            elif reading_question_input:
                # reading from questions section in file.
                pre_variable = line.split("$")
                if len(pre_variable) != 1:
                    question_variables.append(pre_variable[1])
                    if len(question_variables) == 3 and "text_input" in question_variables:
                        # make a text_input question
                        questions.append(Question(
                            key,
                            question_variables[0],
                            question_variables[1],
                            question_variables[2]
                            ))
                        question_variables = []
                    elif len(question_variables) == 4:
                        # make an other question
                        questions.append(Question(
                            key,
                            question_variables[0],
                            question_variables[1],
                            question_variables[2],
                            question_variables[3]
                            ))
                        question_variables = []
                    key += 1  # new unic key for next question
    return (configurations, questions)

def create_datasheet(images, dict_image_id, evaluator_name, datasheet_name=None):
    # make a data sheet in the current folder
    if not datasheet_name:
        # create a name for datasheet if none given
        time = datetime.now()
        datasheet_name = "plaque_identification_of_brain_tissues_" + time.strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
    with open(datasheet_name, 'w', newline='') as datasheet:
        sheet = csv.writer(datasheet, dialect='unix')
        sheet.writerow(["image_name", "identification", "date", "name_evaluator"])
        sheet.writerow([images[0], dict_image_id[images[0]], time.strftime("%Y-%m-%d_%H-%M-%S"), evaluator_name])
        for image in images[1:]:
            sheet.writerow([image, dict_image_id[image]])


### --- initialization of session --- ###

if 'image_to_id_dictionary' not in st.session_state:
    st.session_state.image_to_id_dictionary = dict()

all_pictures = get_all_picture()

if 'picture_seq' not in st.session_state:
    # randomize the picture order
    st.session_state.picture_seq = rd.sample(all_pictures, len(all_pictures))
    st.session_state.number_of_pictures = len(st.session_state.picture_seq)
    st.session_state.progress = 1
if 'current_picture' not in st.session_state:
    st.session_state.current_picture = st.session_state.picture_seq.pop()
if 'keep_identifying' not in st.session_state:
    st.session_state.keep_identifying = True

options = ["plaque", "could be a plaque", "not a plaque", "pass"]


### --- Web page --- ###

st.title("Identify the Brain tissue")

if st.session_state.keep_identifying:
    with st.sidebar:
        chosen_id = st.radio(
            "Identification options:",
            options)
        if chosen_id == "pass":
            st.write("skip this image?")
        else:
            st.write(f"identified brain tissue image as {chosen_id}")

        picture_slider = st.slider(
            "image size (scale)",
            1, 50, 1
        )

        next_picture_button = st.button("Next image")
        if next_picture_button:
            # couple responce (<chosen_id>) to the current_picture
            st.session_state.image_to_id_dictionary[st.session_state.current_picture] = chosen_id
            # change scope to new picture or go to #finished with identification
            if st.session_state.picture_seq != []:
                st.session_state.current_picture = st.session_state.picture_seq.pop()
            st.session_state.progress += 1
            if st.session_state.progress > st.session_state.number_of_pictures:
                st.session_state.keep_identifying = False
                st.experimental_rerun()

    with st.container():
        # show current picture to identify
        original_picture, resizeable_picture = st.columns(2)
        variation = st.session_state.current_picture.types

        with original_picture:
            st.write("original image")
            for var in variation:
                st.write(var)
                st.session_state.current_picture.show(var, 1)

        with resizeable_picture:
            st.write(f"image scaled x{picture_slider} times")
            for var in variation:
                st.write(var)
                st.session_state.current_picture.show(var, picture_slider)
        ''
        ''
        st.write(f"(image {st.session_state.progress} of {st.session_state.number_of_pictures} images)")

else:
    # finished with identification #
    st.subheader("All Brain tissues have been identified.")
    evaluaters_name = st.text_input("Enter your name")
    if evaluaters_name:
        create_datasheet(all_pictures, st.session_state.image_to_id_dictionary, evaluaters_name)
        st.write("evaluation submitted")

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
