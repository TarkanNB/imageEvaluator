# Image Evaluator
A tool for generating a webpage for rating images and storing the responses in a database/spreadsheet

## Usage
### Images:
In the images folder store your images that need to be rated following this namingstructure for each image:
  {sample_name}__{type}.{extension}
### Questions:
In the configurations.ini file add your questions under [Questions] and above [End_questions]:
```ini
[QUESTIONS]
  [Question0]
  Question_type = text_input
  Question_discription = Enter optional comment.

  [question1]
  Question_type = selection_box
  Question_discription = selectionbox question
  Options = option1, option2, option3
```
Or add to add hotkeys add <'keystroke> after an option in Options
```ini
  [question2]
  Question_type = multiple_choice
  Question_discription = multiple_choice_question
  Options = option1 <1>, option2 <2>, option3 <3>
[End_questions]

```
### Further Configurate:
In the configurations.ini file other adjustments can be done,
like image_display and database storage

### When Done:
when images, guestions and other adjustments are made run following streamlit command:
```bash
streamlit run web_page_image_qestionaire.py
```
