import os
from flask import Flask, render_template, flash, request, redirect, url_for, send_from_directory, after_this_request
import gunicorn
from werkzeug.utils import secure_filename
from xml_process import Converter

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/uploads/'
DOWNLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/downloads/'

ALLOWED_EXTENSIONS = {'xml'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_file(path):
    file = Converter(path)
    return file.convert(output_path=app.config['DOWNLOAD_FOLDER'])

# home page


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            process_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            output = os.path.splitext(filename)[0] + '.rpp'

            @after_this_request
            def remove_file(response):
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    # os.remove(os.path.join(app.config['DOWNLOAD_FOLDER'], output))
                    file_handle.close()
                except Exception as error:
                    app.logger.error("Error removing or closing downloaded file handle", error)
                return response
            return redirect(url_for('uploaded_file', filename=output))
    return render_template("index.html")

# download processed file
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    @after_this_request
    def remove_file(response):
        try:
                # os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            os.remove(os.path.join(app.config['DOWNLOAD_FOLDER'], filename))
            file_handle.close()
        except Exception as error:
            app.logger.error("Error removing or closing downloaded file handle", error)
        return response
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
