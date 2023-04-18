""" This program takes images from the imgage directory,
    and shows them in a random order one by one on a webpage.
    Were it will ask the evaluator for questions for each image as given in the configuration.json file.
    The evaluations for a image will be stored in an answer database whenever the evaluator clicks on the next image buton
    finaly, it will store these responces in a datasheet after the last image has been shown. 
"""

from datetime import datetime
import os
import csv
import random as rd
import sqlite3
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components


class Picture:
    def __init__(self, sample_name, types, extension):
        self.sample = sample_name   # string
        self.types = types   # list of str
        self.full_name_of = dict()
        self.full_names = []
        for t in types:
            full_name = sample_name + "__" + t + "." + extension
            self.full_names.append(full_name)
            self.full_name_of[t] = full_name
        self.full_names = tuple(self.full_names)

    def true_size(self):
        img = Image.open(self.full_names[0])
        return img.size

    def standard_show(self, the_type, size_str):
        # Displays a picture when called which has been scaled to the given size (size_str)
        path_to_image = "images/" + self.full_name_of[the_type]
        img = Image.open(path_to_image)
        width, height = img.size
        size = size_str.strip(" ").strip("(").strip(")").strip(" ").split(",")
        if not size_str:
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

    def show(self, the_type, scale=1):
        # Displays the image on the webpage with specified scale.
        path_to_image = "images/" + self.full_name_of[the_type]
        img = Image.open(path_to_image)
        if scale == 1:
            st.image(img, output_format='png')
        else:
            width, height = img.size
            image_size = (width * scale, height * scale)
            new_img = img.resize(image_size)
            st.image(new_img, output_format='png')

class Question:
    def __init__(self, key, name_in_database, type_of_question, question_discription, possible_answers=None):
        self.key = key # needs to be unique and be in correct order to input class index of streamlit generated html file
        self.name_in_database = name_in_database
        self.type = type_of_question
        self.discription = question_discription
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
            return st.text_input(self.discription)
        elif self.type == "multiple_choice":
            return st.radio(self.discription, self.options)
        elif self.type == "selection_box":
            return st.selectbox(self.discription, self.options)
        elif self.type == "check_box":
            return st.checkbox(self.discription, self.options)
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

@st.cache_data
def get_all_picture(type_selection=None):
    # Get the list of images in the images directory
    images_log = os.listdir(get_the_path_to_main_directory() + '/images')

    pictures = []
    sample_name = ""
    types = []
    extension = ""
    for name in sorted(images_log):

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
    # Returns a tuple with:
    # [0]: all configuration variables from the configuration.json file as a dictionary,
    # [1]: all questions in configuration.json file ass a list of Questions (class).
    configuration = dict()
    questions = []
    question_variables = []
    key = 0  # unique key for each question.
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
                configuration[variable] = line.split("$")[1]
                reading_input = False
            elif reading_question_input:
                # reading from questions section in file.
                pre_variable = line.split("$")
                if len(pre_variable) != 1:
                    question_variables.append(pre_variable[1])
                    if len(question_variables) == 3 and "text_input" in question_variables:
                        # make a text_input question
                        text_input_question = Question(
                            key,
                            question_variables[0],
                            question_variables[1],
                            question_variables[2]
                            )
                        questions.append(text_input_question)
                        question_variables = []
                        # new unique key for next question
                        # , and to keep track of the input class for hotkey binding
                        key += 1
                    elif len(question_variables) == 4:
                        # make an other question
                        non_text_input_question = Question(
                            key,
                            question_variables[0],
                            question_variables[1],
                            question_variables[2],
                            question_variables[3].strip(" ").strip("(").strip(")").strip(" ").split(",")
                            )
                        questions.append(non_text_input_question)
                        question_variables = []
                        # new unique key for next question
                        # , and to keep track of the input for hotkey binding
                        key += len(non_text_input_question.options)
    return (configuration, questions)

def get_input_to_hotkey_bindings(questions_sequence):
    # given a list of Questions it returns a map with the correct responce to each key
    option_to_hotkey = dict()
    for question in questions_sequence:
        option_to_hotkey.update(question.hotkeys)
    return option_to_hotkey

def write_hotkey_configurations_html_file(hotkeys_dict, questions_sequence):
    # Writes a generated_hotkey.html file to modify the streamlit generated HTML file,
    # to inject specific key bord listener (= hotkeys) 
    # based on input class index from hotkeys_dict 
    # to specific possible answers of the renderd questions (= input classes in HTML)  
    last_question = questions_sequence[-1]

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

    const next_picture = buttons.find((e1) => e1.innerText === "Next_image");
    """
    html_file_middle = """streamlitDoc.addEventListener("keypress", function (e) {
        switch(e.key) {
            case "Enter":
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
        for i in range(input_lenght):
            if i in hotkeys_dict:
                hotkey_file.write(f"const answer{i} = answers[{i}];")
                bind_input.append(i)
        hotkey_file.write(html_file_middle)
        for j in bind_input:
            explicit_hotkey_string = '"' + hotkeys_dict[j] + '"'
            hotkey_file.write(f"case {explicit_hotkey_string}: \n")
            hotkey_file.write(f"answer{j}.click(); \n")
            hotkey_file.write("break; \n")
        hotkey_file.write(html_file_ending)

def read_html():
    with open("generated_hotkey.html") as file:
        return file.read()

def remove_key_label(options_and_hotkey_list):
    options_list = []
    for option in options_and_hotkey_list:
        options_list.append(option.split("<")[0].strip(" "))
    return options_list

def create_datasheet(picture_class_seq, dict_image_id, evaluator_name, datasheet_name=None):
    # make a data sheet in the current folder
    if not datasheet_name:
        # create a name for datasheet if none given
        time = datetime.now()
        datasheet_name = "plaque_identification_of_brain_tissues_" + time.strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
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
        sqlit_code = "(image_name, "
    elif table_options == "Only_sample":
        sqlit_code = "(sample_name)"
    elif table_options == "Sample_with_seprate_types":
        sqlit_code = "(sample_name, types, "
    else:
        raise Exception(f"Error:{table_options} is not a correct argument for Images_storage in configuration.json")
    for a_question in questions_sequence:
        sqlit_code += a_question.name_in_database + ", "
    return sqlit_code + "date, evaluators_name)"

def get_not_yet_evaluated_pictures(pictures, cursor_db, database, name_of_evaluator):
    remaining_pictures = []
    seen_sample_list = [row[0] for row in cursor_db.execute("SELECT sample_name, evaluators_name FROM " + database + " WHERE evaluators_name='" + name_of_evaluator + "'")]    
    for picture in pictures:
        if not picture.sample in seen_sample_list:
            remaining_pictures.append(picture)
    return remaining_pictures
    

### --- initialization of session --- ###

if 'image_to_id_dictionary' not in st.session_state:
    st.session_state.image_to_id_dictionary = dict()

if 'configurations' not in st.session_state:
    # dictionary with all the configurations without the questions
    st.session_state.configurations = get_configurations()[0]

if 'questions_to_ask' not in st.session_state:
    st.session_state.questions_to_ask = get_configurations()[1]
    st.session_state.hotkeys = get_input_to_hotkey_bindings(st.session_state.questions_to_ask)
    write_hotkey_configurations_html_file(st.session_state.hotkeys, 
        st.session_state.questions_to_ask)

if 'name_entered' not in st.session_state:
    st.session_state.name_entered = False

if 'keep_identifying' not in st.session_state:
    st.session_state.keep_identifying = True

# Create a SQLite database to store answers if there isn't any
database_code = "CREATE TABLE IF NOT EXISTS answers " + db_table_naming_code(
    st.session_state.questions_to_ask,
    st.session_state.configurations["Image_storing"])
conn = sqlite3.connect('answers.db')
cur = conn.cursor()
cur.execute(database_code)
conn.commit()


### --- Web page --- ###

st.title(st.session_state.configurations["Title"])

# Starting page for entering the evaluators name.
if not st.session_state.name_entered:
    # get name from the evaluator
    evaluator = st.text_input("Enter your name.")
    if evaluator:
        st.session_state.evaluators_name = evaluator.strip(" ").lower()
        to_evaluate_pictures = get_not_yet_evaluated_pictures(
            get_all_picture(),
            cur,
            'answers',
            st.session_state.evaluators_name
            )
        st.session_state.picture_seq = rd.sample(to_evaluate_pictures, len(to_evaluate_pictures))
        st.session_state.number_of_pictures = len(st.session_state.picture_seq)
        if st.session_state.number_of_pictures != 0:
            # in case that there are still unevaluated images by the evaluator
            st.session_state.current_picture = st.session_state.picture_seq.pop()
            st.session_state.progress = 1
            st.session_state.name_entered = True
        else:
            # stop the program if there are no images
            st.session_state.keep_identifying = False
        st.experimental_rerun()

# Evaluation of current picture page.
elif st.session_state.keep_identifying:
    # write a discription from the configuration file
    if st.session_state.configurations["Discription"]:
        st.write(st.session_state.configurations["Discription"])

    responses = []
    with st.sidebar:
        # render questions
        for i, question in enumerate(st.session_state.questions_to_ask):
            responses.append(question.ask())
            st.write(f"Selected: {responses[i].split('<')[0]}")

        if st.session_state.configurations["Rescaleability"] == "Enable":
            picture_slider = st.slider(
                "image size (scale)",
                1, 50, 1
            )

        next_picture_button = st.button("Next_image")
        if next_picture_button:
            current_picture = st.session_state.current_picture
            # couple responce (<chosen_id>) to the current_picture
            st.session_state.image_to_id_dictionary[current_picture.full_names] = remove_key_label(responses)
            
            # insert picture with responce in database
            if st.session_state.configurations["Image_storing"] == "Sample_with_seprate_types":
                first_part = [current_picture.sample, str(tuple(current_picture.types))]
            else:
                first_part = [str(current_picture.full_names)]

            database_input = str(tuple(
                first_part
                + remove_key_label(responses) 
                + [datetime.now().strftime("%Y-%m-%d"), 
                st.session_state.evaluators_name]
                ))
            cur.execute("INSERT INTO answers VALUES " + database_input)
            conn.commit()

            # change scope to new picture or go to #finished with identification
            if st.session_state.picture_seq != []:
                st.session_state.current_picture = st.session_state.picture_seq.pop()
            st.session_state.progress += 1
            # Ending the session if all pictures have passed
            if st.session_state.progress > st.session_state.number_of_pictures:
                st.session_state.keep_identifying = False
                st.experimental_rerun()
        st.write("<Enter>")

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
                    variation[i],
                    st.session_state.configurations["Default_scale"]
                    )
        
        # shows scaleable questions
        if st.session_state.configurations["Rescaleability"] == "Enable":
            if picture_slider == 1:
                st.write("original size")
            else:
                st.write(f"image scaled x{picture_slider} times")
            for var in variation:
                st.write(var)
                st.session_state.current_picture.show(
                    var,
                    picture_slider
                    )

# End page 
else:
    # finished with identification #
    st.subheader("All images have been identified.")
    conn.close()
    create_datasheet(get_all_picture(),
        st.session_state.image_to_id_dictionary,
        st.session_state.evaluators_name)
    st.write("evaluation submitted")

### information for development.

''
''
''
'Only for development'
'Internal values:'
''
'questions'
st.write(st.session_state.questions_to_ask[0].options)
''
'configurations'
st.write(st.session_state.configurations)
''
'picture_seq:'
st.write(str(st.session_state.picture_seq))
''
'number of pictures in this folder:'
st.write(str(st.session_state.number_of_pictures))
''
'dictionary'
st.write(str(st.session_state.image_to_id_dictionary))
''
'hotkeys'
st.write(st.session_state.hotkeys)
''
'evaluator'
st.write(st.session_state.evaluators_name)

# Enable the hotkeys via the generated_hotkey.html file
components.html(
            read_html(),
            height=0,
            width=0,
        )
