import os
import shutil
import time
from flask_apscheduler import APScheduler
import numpy as np
import pandas as pd
import tensorflow as tf
from keras.preprocessing.image import ImageDataGenerator
from keras.models import load_model
import requests
from flask import Flask, render_template, request, redirect, flash, send_from_directory
from werkzeug.utils import secure_filename

from data import disease_map, details_map

# Download Model File
if not os.path.exists('model.h5'):
    print("Downloading model...")
    url = "https://drive.google.com/uc?id=1JNggWQ9OJFYnQpbsFXMrVu-E-sR3VnCu&confirm=t"
    r = requests.get(url, stream=True)
    with open('./model.h5', 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    print("Finished downloading model.")

# Load model from downloaded model file
model = load_model('model.h5')

# Create folder to save images temporarily
if not os.path.exists('./static/test'):
        os.makedirs('./static/test')

def predict(test_dir):
    test_img = [f for f in os.listdir(os.path.join(test_dir)) if not f.startswith(".")]
    test_df = pd.DataFrame({'Image': test_img})
    
    test_gen = ImageDataGenerator(rescale=1./255)

    test_generator = test_gen.flow_from_dataframe(
        test_df, 
        test_dir, 
        x_col = 'Image',
        y_col = None,
        class_mode = None,
        target_size = (256, 256),
        batch_size = 20,
        shuffle = False
    )
    predict = model.predict(test_generator, steps = np.ceil(test_generator.samples/20))
    test_df['Label'] = np.argmax(predict, axis = -1) # axis = -1 --> To compute the max element index within list of lists
    test_df['Label'] = test_df['Label'].replace(disease_map)

    prediction_dict = {}
    for value in test_df.to_dict('index').values():
        image_name = value['Image']
        image_prediction = value['Label']
        prediction_dict[image_name] = {}
        prediction_dict[image_name]['prediction'] = image_prediction
        prediction_dict[image_name]['description'] = details_map[image_prediction][0]
        prediction_dict[image_name]['symptoms'] = details_map[image_prediction][1]
        prediction_dict[image_name]['source'] = details_map[image_prediction][2]
    return prediction_dict


# Create an app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # maximum upload size is 50 MB
app.secret_key = "agentcrop"
ALLOWED_EXTENSIONS = {'png', 'jpeg', 'jpg'}
folder_num = 0
folders_list = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# initialize scheduler
scheduler = APScheduler()
scheduler.api_enabled = True
scheduler.init_app(app)

# Adding Interval Job to delete folder
@scheduler.task('interval', id='clean', seconds=1800, misfire_grace_time=900)
def clean():
    global folders_list
    try:
        for folder in folders_list:
            if (time.time() - os.stat(folder).st_ctime) / 3600 > 1:
                shutil.rmtree(folder)
                folders_list.remove(folder)
                print("\n***************Removed Folder '{}'***************\n".format(folder))
    except:
        flash("Something Went Wrong! couldn't delete data!")

scheduler.start()

@app.route('/', methods=['GET', 'POST'])

def get_disease():
    global folder_num
    global folders_list
    if request.method == 'POST':
        if folder_num >= 1000000:
            folder_num = 0
        # check if the post request has the file part
        if 'hiddenfiles' not in request.files:
            flash('No files part!')
            return redirect(request.url)
        # Create a new folder for every new file uploaded,
        # so that concurrency can be maintained
        files = request.files.getlist('hiddenfiles')
        app.config['UPLOAD_FOLDER'] = "./static/test"
        app.config['UPLOAD_FOLDER'] = app.config['UPLOAD_FOLDER'] + '/predict_' + str(folder_num).rjust(6, "0")
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
            folders_list.append(app.config['UPLOAD_FOLDER'])
            folder_num += 1
        for file in files:
            if file.filename == '':
                flash('No Files are Selected!')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                flash("Invalid file type! Only PNG, JPEG/JPG files are supported.")
                return redirect('/')
        try:
            if len(os.listdir(app.config['UPLOAD_FOLDER'])) > 0:
                diseases = predict(app.config['UPLOAD_FOLDER'])
                return render_template('show_prediction.html',
                folder = app.config['UPLOAD_FOLDER'],
                predictions = diseases)
        except:
            return redirect('/')
        
    return render_template('index.html')

@app.route('/favicon.ico')

def favicon(): 
    return send_from_directory(os.path.join(app.root_path, 'static'), 'Agent-Crop-Icon.png')

#API requests are handled here
@app.route('/api/predict', methods=['POST'])

def api_predict():
    global folder_num
    global folders_list
    if folder_num >= 1000000:
            folder_num = 0
    # check if the post request has the file part
    if 'files' not in request.files:
        return {"Error": "No files part found."}
    # Create a new folder for every new file uploaded,
    # so that concurrency can be maintained
    files = request.files.getlist('files')
    app.config['UPLOAD_FOLDER'] = "./static/test"
    app.config['UPLOAD_FOLDER'] = app.config['UPLOAD_FOLDER'] + '/predict_' + str(folder_num).rjust(6, "0")
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        folders_list.append(app.config['UPLOAD_FOLDER'])
        folder_num += 1
    for file in files:
        if file.filename == '':
            return {"Error": "No Files are Selected!"}
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            return {"Error": "Invalid file type! Only PNG, JPEG/JPG files are supported."}
    try:
        if len(os.listdir(app.config['UPLOAD_FOLDER'])) > 0:
            diseases = predict(app.config['UPLOAD_FOLDER'])
            return diseases
    except:
        return {"Error": "Something Went Wrong!"}

        #"//how to get the stock data of Tesla in python?"