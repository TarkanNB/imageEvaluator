""" This program takes images from the images directory,
    and shows them in a random order one by one on a webpage.
    Were it will ask the evaluator for questions for each image as given in the configuration.ini file.
    The evaluations for a image will be stored in an answer database whenever the evaluator clicks on the next image buton
    finaly, it will store these responses in a datasheet after the last image has been shown. 
"""

from datetime import datetime
import os
import csv
import random as rd
import numpy as np
import pandas as pd
import sqlite3
import configparser
from PIL import Image, ImageDraw
import streamlit as st
import streamlit.components.v1 as components

###################################################################

def private_draw_scale_bar(image_path, bar_lenght, bar_text):
    if not bar_lenght:
        return Image.open(image_path)
    with Image.open(image_path) as img:
        if img.mode == "I":
            print("ok")
            color=2**30
        else:
            color=(255,255,255)
        draw = ImageDraw.Draw(img)
        draw.line((img.size[0]-int(bar_lenght)-5, img.size[1]-5, img.size[0]-5, img.size[1]-5),fill=color)
        draw.text((img.size[0]-int(bar_lenght), img.size[1]-20), bar_text, fill=color)
    return img

@st.cache_data
def private_standard_show(image_path, default_size, scale_bar_length, scale_bar_text):
    img = private_draw_scale_bar(image_path, scale_bar_length, scale_bar_text)
    width, height = img.size
    size = default_size.strip(" ").strip("(").strip(")").strip(" ").split(",")
    if size == "":
        st.image(img, output_format='png')
        return None
    elif len(size) == 1:
        image_size = (int(size[0]), int(size[0]))
    elif len(size) == 2:
        image_size = (int(size[0]), int(size[1]))
    else:
        raise Exception("Error: Could not interpret the Default scale in configuration file.")
    new_img = img.resize(image_size)
    st.image(new_img, output_format='png')

@st.cache_data
def private_scaled_show(image_path, scale, scale_bar_length, scale_bar_text):
    img = private_draw_scale_bar(image_path, scale_bar_length, scale_bar_text)
    if scale == 1:
        st.image(img, output_format='png')
    else:
        width, height = img.size
        image_size = (width * scale, height * scale)
        new_img = img.resize(image_size)
        st.image(new_img, output_format='png')

@st.cache_data
def private_write_images_intensity_html_file(distance_Img_scaledImg, maximum_intensity):
    html_file_start = """<script>
    // vaiable region (this code is modified by the web_page_imageEvaluator.py)
    """
    with open("images_intensity_ending.html", 'r') as constant_html:
        html_file_ending = constant_html.readlines()
   
    with open("images_js.html", "w") as images_file:
        images_file.write(html_file_start)
        images_file.write(f"distance_Img_scaledImg = {distance_Img_scaledImg}\n")
        images_file.write(f"maximum_sliders = {maximum_intensity}")
        for line in html_file_ending:
            images_file.write(line)


class Picture:
    # Grouping of images of the same sample
    def __init__(self, sample_name, types, extension, seperators, image_directory):
        self.sample = sample_name   # string
        self.types = types   # list of str
        self.full_name_of = dict() # get file_name(string) of image of [specified type]
        self.full_names = [] # get all image_file_names
        for t in types:
            full_name = sample_name + seperators[0] + t + seperators[1] + extension
            self.full_names.append(full_name)
            self.full_name_of[t] = full_name
        self.full_names = tuple(self.full_names)
        self.image_directory = image_directory
        self.defaults = dict() # default image display values

    def set_defaults(self, image_to_default_variable_map, configuration):
        # initialaze defaults when there exists a standart default for one of the images in image_to_default_variable_map
        template_defaults = {
            'size' : configuration["IMAGE_DISPLAY"]["Default_scale"],
            'broad_image' : None,
            'location' : None,
            'scale_bar_text' : None,
            'scale_bar_length': None,
            }
        if not image_to_default_variable_map.empty:
            for img_name in self.full_names:
                if img_name in image_to_default_variable_map.index:
                    data_sheet_values_for_image = image_to_default_variable_map.loc[img_name]
                    for key in template_defaults.keys():
                        if key in data_sheet_values_for_image:
                            template_defaults[key]=str(data_sheet_values_for_image[key])

        self.defaults = template_defaults

    def standard_show(self, the_type):
        # Displays a picture when called which has been scaled to default_size
        path_to_image = self.image_directory + '/' + self.full_name_of[the_type]
        private_standard_show(path_to_image, self.defaults['size'], self.defaults['scale_bar_length'], self.defaults['scale_bar_text'])      

    def scaled_show(self, the_type, scale=1):
        # Displays the image on the webpage with specified scale.
        path_to_image = self.image_directory + '/' + self.full_name_of[the_type]
        private_scaled_show(path_to_image, scale, self.defaults['scale_bar_length'], self.defaults['scale_bar_text'])
    
    def show_broader_image(self):
        # shows the broader image with an square where the images are located
        if self.defaults["broad_image"]:
            path_to_broad_image =self.image_directory + '/broad_images/' + self.defaults["broad_image"]
            img = Image.open(path_to_broad_image)
            pre_coordinates = self.defaults["location"].strip('[').strip(']').split(',')
            coordinates = [int(x.strip('(').strip(')')) for x in pre_coordinates]
            draw = ImageDraw.Draw(img)
            draw.rectangle(coordinates, outline="red", width=2)
            st.image(img, output_format='png')
    
    def write_images_intensity_html_file(self, configurations):
        if configurations["IMAGE_DISPLAY"]["Rescaleability"] == "Enable":
            if self.defaults['broad_image']:
                distance_between_img_and_scaled_img = len(self.types)+1
            else:
                distance_between_img_and_scaled_img = len(self.types)
        else:
            distance_between_img_and_scaled_img = 0
        
        private_write_images_intensity_html_file(distance_between_img_and_scaled_img, configurations["IMAGE_DISPLAY"]["Max_brightness_and_contrast"])

class Question:
    def __init__(self, key, name_in_database, type_of_question, question_description, possible_answers=None):
        self.key = key # needs to be unique and be in correct order to input class index of streamlit generated html file
        self.name_in_database = name_in_database
        self.type = type_of_question
        self.description = question_description
        self.options = possible_answers
        # hotkeys is a dictionary where a key points to a specific index of HTML input class
        self.hotkeys = dict()
        if possible_answers:
            for i, possible_ans in enumerate(possible_answers):
                hotkey = possible_ans.split("<")[-1].strip(" ").rstrip(">").strip(" ")
                if hotkey in "cr":
                    raise Exception(f"Error: c and r keys can not be designated as hotkeys, <{hotkey}> for the <{possible_ans}> option")    
                elif len(hotkey) == 1:
                    # Bind hotkey to corresponding indexe of the input class of the streamlit generated HTML code.
                    self.hotkeys[self.key + i] = hotkey

    def ask(self):
        # Displays the question with the possible answers/text box
        if self.type == "text_input":
            return st.text_input(self.description)
        elif self.type == "multiple_choice":
            return st.radio(self.description, self.options)
        elif self.type == "selection_box":
            return st.selectbox(self.description, self.options)
        elif self.type == "check_box":
            checkbox_options = []
            st.write(self.description)
            for k, option in enumerate(self.options):
                checkbox_options.append(st.checkbox(option, key=self.key+k))
            return checkbox_options
        else:
            raise Exception("Error: wrong question type, see question types in configuration file.")

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

def get_questionnaires_options():
    # Get all the possible questionnaires in imageEvaluator/data folder, 
    # and return a dictionairy with items option : path_to_folder_of_option
    questionnaires = dict()
    options = os.listdir(get_the_path_to_main_directory() + '/data')
    for option in options:
        if option[0] != '.':
            questionnaire_files = os.listdir(get_the_path_to_main_directory() + '/data/' + option)
            if not "configuration.ini" in questionnaire_files:
                #raise Exception(f"No configuration.ini file for {option} questionnaire.")
                continue
            if not "images" in questionnaire_files:
                #raise Exception(f"No images directory for {option} questionnaire.")
                continue
            elif not os.listdir(get_the_path_to_main_directory() + '/data/' + option + '/images'):
                #raise Exception(f"The images directory for {option} questionnaire is empty")
                continue
            else:
                questionnaires[option] = get_the_path_to_main_directory() + f"/data/{option}"
    return questionnaires 

def split_in_name_rest(name, seperator):
    seperations = name.split(seperator)
    head = seperations.pop()
    return (seperator.join(seperations), head)

def get_all_picture(configuration, path_to_images_directory=None):
    # Get all  the images from images_directory and returns a list of Pictures
    # (images get grouped by there sample_name in a Picture class)

    # Get the list of images in the images directory
    if path_to_images_directory:
        images_log = os.listdir(path_to_images_directory)
    else:
        path_to_images_directory = './images'
        images_log = os.listdir(get_the_path_to_main_directory() + '/images')

    seperators = configuration["IMAGE_DISPLAY"]["Image_naming_structure"].strip(' ').strip('sample').strip('extension').split('type')

    pictures = []
    sample_name = ""
    types = []
    extension = ""
    for name in sorted(images_log):
        if name == "broad_images": # skip directory
            continue
        
        # Check for correct image_file format, 
        # if correct format: extract sample type and extention names for Picture class.
        sample_typeextension = split_in_name_rest(name,seperators[0])
        type_extension =  split_in_name_rest(sample_typeextension[-1], seperators[1])
        extension = type_extension[-1]
        if extension not in ["jpg", "jpeg", "jfif", "pjpeg", "pjp", "png", "svg"]:
            raise Exception(f"Error: uncleare extension in picture_folder: {extension} of file: {name}")

        # check if it is a new variation of sample or a new sample.
        if sample_name == sample_typeextension[0]:
            types.append(type_extension[0])
        elif types:
            pictures.append(Picture(sample_name, types, extension, seperators, path_to_images_directory))
            sample_name = sample_typeextension[0]
            types = [type_extension[0]]
        else:
            sample_name = sample_typeextension[0]
            types = [type_extension[0]]
    # add the last sample to the picture class
    if types:
        pictures.append(Picture(sample_name, types, extension, seperators, path_to_images_directory))
    
    if pictures:
        return pictures
    else:
        raise Exception("Error: could detect no picture files in local folder.")

def get_questions(configuration):
    # takes all the questions descriptions from the configuration 
    # and returns a list of Questions classes 
    questions_list = []
    config = configuration.sections()
    configurated_questions = config[config.index('QUESTIONS')+1 : config.index('End_questions')]
    key = 0  # unique key for each question.
    for config_question in configurated_questions:
        if configuration[config_question]['Question_type'] == 'text_input':
            text_input_question = Question(
                key,
                config_question,
                'text_input',
                configuration[config_question]['Question_description']
                )
            questions_list.append(text_input_question)
            # new unique key for next question,
            #  and to keep track of the input for hotkey binding
            key += 1
        else:
            # non text_input questions
            question_class = Question(
                key,
                config_question,
                configuration[config_question]['Question_type'],
                configuration[config_question]['Question_description'],
                configuration[config_question]['Options'].strip(" ").split(",")
                )
            questions_list.append(question_class)
            # new unique key for next question,
            #  and to keep track of the input for hotkey binding
            if configuration[config_question]['Question_type'] == "selection_box":
                key += 1
            else:
                key += len(question_class.options)        
    return questions_list

def get_default_image_value_mapping(path_to_questionnaire):
    # Takes path to <folder_name>_images_default_values.csv file,
    # and returns a panda_dataframe of the file if the file does not exists return empty dataframe
    file_name = path_to_questionnaire.split("/")[-1] + "_images_default_values.csv"
    if not file_name in os.listdir(path_to_questionnaire):
        return pd.DataFrame()
    file = path_to_questionnaire + "/" + path_to_questionnaire.split("/")[-1] + "_images_default_values.csv"
    return pd.read_csv(file, index_col='image')

def extract_list(string, as_number=False):
    string_list = string.strip("[").strip("[").strip("(").strip(")").split(",")
    if as_number:
        if "." in string:
            return [float(n) for n in string_list]
        return [int(n) for n in string_list]
    return string_list

def get_input_to_hotkey_bindings(questions_sequence):
    # given a list of Questions it returns a map with the correct responce to each key
    option_to_hotkey = dict()
    for question in questions_sequence:
        option_to_hotkey.update(question.hotkeys)
    return option_to_hotkey

def write_hotkey_configurations_html_file(hotkeys_dict, questions_sequence, next_image_button_hotkey, workflow_config):
    # Writes a generated_hotkey.html file to modify the streamlit generated HTML file,
    # to inject specific key bord listener (= hotkeys) 
    # based on input class index from hotkeys_dict 
    # to specific possible answers of the renderd questions (= input classes in HTML)  
    last_question = questions_sequence[-1]
    
    # make correct questions_input with lenght = number of multiple_choice_questions,
    # and pressing of hotkey maps to correct questions_input index.
    questions_input = '['
    is_multiple_choice_question = dict()
    input_region = 0
    for q in questions_sequence:
        if q.type == "multiple_choice":
            for hotkey_input in list(q.hotkeys):
                is_multiple_choice_question[hotkey_input] = input_region
            questions_input += "false,"
            input_region += 1
    questions_input = questions_input.rstrip(',') + ']'

    if last_question.options:
        input_lenght = last_question.key + len(last_question.options)
    else:
        input_lenght = last_question.key

    html_file_start = """<script>
    const streamlitDoc = window.parent.document;
    
    buttons = Array.from(streamlitDoc.querySelectorAll(".stButton > button"));
    console.log(buttons);
    answers = Array.from(streamlitDoc.querySelectorAll("input"));
    console.log(answers);
    """

    html_file_button = f"var questions_input = {questions_input}" + """
    checker = arr => arr.every(v => v === true);
    const next_picture = buttons.find((e1) => e1.innerText === "Next_image");
    """
    html_file_middle = """streamlitDoc.addEventListener("keypress", function (e) {
        switch(e.key) {
            case '""" + next_image_button_hotkey + """':
                questions_input = """ + questions_input + """;
                next_picture.click();
                break;
        """
    html_file_ending = """        }
        });
        </script>
        """
    
    bind_input = []
    with open("generated_hotkey.html", "w") as hotkey_file:
        hotkey_file.write(html_file_start)
        hotkey_file.write(html_file_button)
        for i in range(input_lenght):
            if i in hotkeys_dict:
                hotkey_file.write(f"const answer{i} = answers[{i}];\n")
                bind_input.append(i)
        hotkey_file.write(html_file_middle)

        for j in bind_input:
            explicit_hotkey_string = '"' + hotkeys_dict[j] + '"'
            hotkey_file.write(f"case {explicit_hotkey_string}: \n")
            hotkey_file.write(f"answer{j}.click(); \n")
            if j in is_multiple_choice_question and workflow_config == "Enable":
                hotkey_file.write(f"questions_input[{is_multiple_choice_question[j]}] = true;\n")
                hotkey_file.write("if (checker(questions_input)) {next_picture.click();\n")
                hotkey_file.write(f"questions_input = {questions_input};" + "}\n")
            hotkey_file.write("break; \n")
        hotkey_file.write(html_file_ending)

def read_html(file_in_directory):
    with open(file_in_directory) as file:
        return file.read()

def remove_key_label(options_and_hotkey_list):
    options_list = []
    for option in options_and_hotkey_list:
        options_list.append(option.split("<")[0].strip(" "))
    return options_list

def create_datasheet(picture_class_seq, dict_image_id, evaluator_name, path_to_questionnaire, datasheet_base_name):
    if picture_class_seq == []:
        return None
    # make a data sheet in the current folder
    
    # create a name for datasheet if none given
    time = datetime.now()
    datasheet_name = path_to_questionnaire +'/'+ datasheet_base_name +'_'+ time.strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
    st.write(datasheet_name)
    with open(datasheet_name, 'w', newline='') as datasheet:
        sheet = csv.writer(datasheet, dialect='unix')
        respons_category = [qest.name_in_database for qest in st.session_state.questions_to_ask]
        sheet.writerow(["image_name"] + respons_category + ["date", "name_evaluator"])
        sheet.writerow([picture_class_seq[0].full_names] + dict_image_id[picture_class_seq[0].full_names] + [time.strftime("%Y-%m-%d_%H-%M-%S"), evaluator_name])
        for picture in picture_class_seq[1:]:
            sheet.writerow([picture.full_names] + dict_image_id[picture.full_names])

def db_table_naming_code(questions_sequence, table_options):
    # creates the tables to be inputed in the database file
    if table_options == "Full_name":
        sqlite_code = "(id, "
    elif table_options == "Only_sample":
        sqlite_code = "(id, "
    elif table_options == "Sample_with_separate_types":
        sqlite_code = "(id, types, "
    else:
        raise Exception(f"Error: {table_options} is not a correct argument for Images_storage in configuration.ini")
    for quest in questions_sequence:
        sqlite_code += quest.name_in_database + ", "
    return sqlite_code + "date, evaluators_name)"

def create_database(configuration, path_to_database_folder):
    # Create a SQLite database to store answers if there isn't any
    database_name = path_to_database_folder.split('/')[-1]
    database_code = f"CREATE TABLE IF NOT EXISTS {database_name} " + db_table_naming_code(
        get_questions(configuration),
        configuration["DATABASE"]["Image_storing"])
    conn = sqlite3.connect(f'{path_to_database_folder}/{database_name}.db')
    c = conn.cursor()
    c.execute(database_code)
    conn.commit()
    return (c, conn, database_name)

def get_not_yet_evaluated_pictures(pictures, cursor_db, database, name_of_evaluator):
    # returns all pictures that evaluator has not evaluated in the image folder.
    remaining_pictures = []
    name_of_evaluator_in_database = name_of_evaluator.lower()
    seen_sample_list = [row[0] for row in cursor_db.execute("SELECT id, evaluators_name FROM " + database + " WHERE evaluators_name='" + name_of_evaluator_in_database + "'")]    
    for picture in pictures:
        if not picture.sample in seen_sample_list:
            remaining_pictures.append(picture)
    return remaining_pictures


#############################################################

### --- Initialization of session --- ###
## Set the variables for this session
##

if 'image_to_id_dictionary' not in st.session_state:
    st.session_state.image_to_id_dictionary = dict()

if 'configurations' not in st.session_state:
    # Set configurations from configuration.ini file for this session
    st.session_state.configurations = configparser.ConfigParser()

if 'name_entered' not in st.session_state:
    st.session_state.name_entered = False # switch for Starting web page

if 'keep_identifying' not in st.session_state:
    st.session_state.keep_identifying = True # switch for picture evaluating web pages

if 'slider_key' not in st.session_state:
    st.session_state.slider_key = 0


##############################################################

### --- Web page --- ###
## Rendering of the web page
##

st.set_page_config(layout="wide")

# Starting web page for entering the evaluators name and choosing questionnaire.
if not st.session_state.name_entered:
    temporary_config = configparser.ConfigParser()
    
    # let evaluator choose a questionnaire from available folders in imageEvaluator/data folder
    questionnaires_options = get_questionnaires_options()
    if len(questionnaires_options) == 0:
        raise Exception("No options for the evaluator")
    elif len(questionnaires_options) == 1:
        selected_questionnaire = list(questionnaires_options)[0]
    else:
        selected_questionnaire = st.selectbox("Select which images to evaluate", list(questionnaires_options))

    if selected_questionnaire:
        path_to_questionnaire = questionnaires_options[selected_questionnaire]
        temporary_config.read(path_to_questionnaire + "/configuration.ini")
        st.write(temporary_config["TEXT"]["Start_Description"])

        # get name from the evaluator
        evaluator = st.text_input(f"Enter your name to start evaluating the images of {selected_questionnaire} questionnaire.")
        if evaluator:
            st.session_state.evaluators_name = evaluator.strip(" ").lower()
            database = create_database(
                temporary_config,
                path_to_questionnaire
                )
            to_evaluate_pictures = get_not_yet_evaluated_pictures(
                get_all_picture(temporary_config, path_to_questionnaire + "/images"),
                database[0],
                database[2],
                evaluator
                )
            if len(to_evaluate_pictures) != 0:
                # In case that there are still unevaluated images by the evaluator:
                # Initialize session_state variables for the evaluator chozen questionnaire
                st.session_state.progress = 1
                st.session_state.name_entered = True
                st.session_state.configurations = temporary_config
                st.session_state.picture_seq = rd.sample(to_evaluate_pictures, len(to_evaluate_pictures)) # randomize the picture order
                st.session_state.default_image_value_mapping = get_default_image_value_mapping(path_to_questionnaire)
                st.session_state.startOfSession_picture_seq = st.session_state.picture_seq.copy()
                st.session_state.number_of_pictures = len(to_evaluate_pictures)
                st.session_state.current_picture = st.session_state.picture_seq.pop()
                st.session_state.current_picture.set_defaults(st.session_state.default_image_value_mapping, st.session_state.configurations)
                st.session_state.questions_to_ask = get_questions(st.session_state.configurations)
                st.session_state.path_to_questionnaire = path_to_questionnaire
                
                # write a HTML file for activating all extracted hotkeys from questions
                st.session_state.hotkeys = get_input_to_hotkey_bindings(st.session_state.questions_to_ask)
                write_hotkey_configurations_html_file(
                    st.session_state.hotkeys, 
                    st.session_state.questions_to_ask,
                    st.session_state.configurations["WORKFLOW"]["Next_image_button_hotkey"],
                    st.session_state.configurations["WORKFLOW"]["Change_image_after_choice_selection"]
                    )
                
                # write a HTML file to add javascript slider
                st.session_state.current_picture.write_images_intensity_html_file(st.session_state.configurations)
                
                st.session_state.name_of_selected_questionnaire = selected_questionnaire

                st.experimental_rerun() # reload web page (go to #Evaluation_of_current_picture_web_page)
            else:
                # in case there are no images to evaluate
                st.write(f"All available images in {selected_questionnaire} have already been evaluated by {evaluator}.")
            

# Evaluation of current picture web page.
elif st.session_state.keep_identifying:
    st.title(st.session_state.configurations["TEXT"]['Title'])
    # write a description from the configuration file
    if st.session_state.configurations["TEXT"]["Middle_Description"]:
        st.write(st.session_state.configurations["TEXT"]["Middle_Description"])

    responses = []
    with st.sidebar:
        # render questions
        check_box_type_indexes = []
        for i, question in enumerate(st.session_state.questions_to_ask):
            responses.append(question.ask())
            if question.type != 'check_box':
                st.write(f"Selected: {responses[i].split('<')[0]}")
            else:
                check_box_type_indexes.append(i)
        picture_types_brightnesses = []
        picture_types_contrasts = []
        for i, picture_type in enumerate(st.session_state.current_picture.types):
            st.write(f"image brightness of {picture_type}")
            picture_types_brightnesses.append(f"image brightness of {picture_type}")
            st.write(f"image contrast of {picture_type}")
            picture_types_contrasts.append(f"image contrast of {picture_type}")

        if st.session_state.configurations["IMAGE_DISPLAY"]["Rescaleability"] == "Enable":
            # slider to control the scale of bottom images
            picture_slider = st.slider(
                "image size (scale)",
                1,
                int(st.session_state.configurations['IMAGE_DISPLAY']['Max_scale']),
                1,
                key="slider_scale"+str(st.session_state.slider_key+1)
            )

        next_picture_button = st.button("Next_image")
        if next_picture_button:
            st.session_state.slider_key += 2 # reset sliders
            current_picture = st.session_state.current_picture
            for i in check_box_type_indexes:
                check_box_responses = ""
                for ii, check in enumerate(responses[i]):
                    if check:
                        if check_box_responses:
                            check_box_responses += ","
                        check_box_responses += st.session_state.questions_to_ask[i].options[ii].split("<")[0].strip()
                responses[i] = check_box_responses

            # couple responce (<chosen_id>) to the current_picture
            st.session_state.image_to_id_dictionary[current_picture.full_names] = remove_key_label(responses)
            
            # insert picture with responce in database
            if st.session_state.configurations["DATABASE"]["Image_storing"] == "Sample_with_separate_types":
                first_part = [current_picture.sample, str(tuple(current_picture.types))]
            else:
                first_part = [str(current_picture.full_names)]
            database_input = str(tuple(
                first_part
                + remove_key_label(responses) 
                + [datetime.now().strftime("%Y-%m-%d"), 
                st.session_state.evaluators_name]
                ))
            
            # Connect with sqlit database and enter responce for picture 
            database_name = st.session_state.path_to_questionnaire.split('/')[-1]
            conn = sqlite3.connect(st.session_state.path_to_questionnaire + f"/{database_name}.db")
            cur = conn.cursor()
            cur.execute(f"INSERT INTO {database_name} VALUES " + database_input)
            conn.commit()

            # change scope to new picture or go to #finished with identification
            if st.session_state.picture_seq != []:
                st.session_state.current_picture = st.session_state.picture_seq.pop()
                st.session_state.current_picture.set_defaults(st.session_state.default_image_value_mapping,  st.session_state.configurations)
                st.session_state.current_picture.write_images_intensity_html_file(st.session_state.configurations)
            st.session_state.progress += 1
            # Ending the session if all pictures have passed
            if st.session_state.progress > st.session_state.number_of_pictures:
                st.session_state.keep_identifying = False  # stop rendering #Evaluation_of_current_picture_web_page
            st.cache_data.clear()
            st.experimental_rerun()  # go to next web page
        button_hotkey_str = st.session_state.configurations["WORKFLOW"]["Next_image_button_hotkey"]
        st.write(f"<{button_hotkey_str}>")

    # rendering the images of the current_picture
    with st.container():
        st.write(f"(image {st.session_state.progress} of {st.session_state.number_of_pictures} images)")
        ''
        ''
        # show current image(s) to identify
        variation = st.session_state.current_picture.types
        
        columns_standart_images = st.columns(len(variation))
        for i, col in enumerate(columns_standart_images):
            with col:
                st.write(variation[i])
                st.session_state.current_picture.standard_show(
                    variation[i]
                    )
        
        if st.session_state.current_picture.defaults["broad_image"]:
            # show broad_image
            st.write("Images from above are located in the marked square.")
            st.session_state.current_picture.show_broader_image()

        # shows scaleable images
        if st.session_state.configurations['IMAGE_DISPLAY']["Rescaleability"] == "Enable":
            if picture_slider == 1:
                st.write("original size")
            else:
                st.write(f"image scaled x{picture_slider} times")
            for var in variation:
                st.write(var)
                st.session_state.current_picture.scaled_show(
                    var,
                    picture_slider
                    )
        # Enable image intensity sliders
        components.html(
            read_html("images_js.html"),
            height=0,
            width=0,
        )

    # Enable the hotkeys via the generated_hotkey.html file
    components.html(
            read_html("generated_hotkey.html"),
            height=0,
            width=0,
        )

# Ending web page 
else:
    # finished with identification #
    st.subheader(st.session_state.configurations["TEXT"]["End_Description"])
    basename_datasheet = st.session_state.configurations["DATABASE"]["Datasheet_name"]
    if basename_datasheet == "":
        basename_datasheet = st.session_state.path_to_questionnaire.split('/')[-1]

    if st.session_state.configurations["DATABASE"]["Create_datasheet"] == "Enable":
        create_datasheet(
            st.session_state.startOfSession_picture_seq,
            st.session_state.image_to_id_dictionary,
            st.session_state.evaluators_name,
            st.session_state.path_to_questionnaire,
            basename_datasheet
            )
