import os
import boto3
import json
from flask import Flask, render_template, flash, request, redirect, url_for, send_from_directory, after_this_request, Response
import gunicorn
from werkzeug.utils import secure_filename
from xml_process import Converter


bucket = os.environ.get('S3_BUCKET')
s3 = boto3.client('s3')
ALLOWED_EXTENSIONS = {'xml'}

app = Flask(__name__)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_file(string):
    converter = Converter(filestring=string)
    return converter.convert_to_string()

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
            s3.put_object(Bucket=bucket, Body=file.read(), Key='Upload/' + filename)
            response = s3.get_object(Bucket=bucket, Key='Upload/' + filename)
            processed_string = process_file(response['Body'].read())
            output = os.path.splitext(filename)[0] + '.rpp'
            s3.put_object(Bucket=bucket, Body=processed_string, Key='Download/' + output)

            processed_file = s3.get_object(Bucket=bucket, Key='Download/' + output)

            @after_this_request
            def remove_file(response):
                try:
                    s3.delete_object(Bucket=bucket, Key='Upload/' + filename)
                    s3.delete_object(Bucket=bucket, Key='Download/' + output)
                except Exception as error:
                    app.logger.error("Error removing or closing downloaded file handle", error)
                return response
            return Response(
                processed_file['Body'].read(),
                mimetype='text/plain',
                headers={'Content-Disposition': 'attachment;filename={}'.format(output)}
            )
    return render_template("index.html")

# download processed file


# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     @after_this_request
#     def remove_file(response):
#         try:
#                 # os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             os.remove(os.path.join(app.config['DOWNLOAD_FOLDER'], filename))
#             file_handle.close()
#         except Exception as error:
#             app.logger.error("Error removing or closing downloaded file handle", error)
#         return response
#     return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment = True)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    # app.run(debug=True)
