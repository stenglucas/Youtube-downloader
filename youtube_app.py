from flask import Flask, render_template, url_for, redirect, request, flash, send_file, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from io import BytesIO
from pytube import YouTube, Playlist
from zipfile import ZipFile
import os, requests



app = Flask(__name__)


app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# Handlers

@app.errorhandler(404)
def page_not_found_404(error):
    return render_template('404.html', error=error), 404


@app.errorhandler(500)
def page_not_found_500(error):
    return render_template('500.html',error=error), 500

# Form
class linkForm(FlaskForm):
    link = StringField('Youtube link', validators=[DataRequired()])
    submit = SubmitField('Descargar')
    
class playlistForm(FlaskForm):
    link = StringField('Playlist', validators=[DataRequired()])
    submit = SubmitField('Convertir')
    
def is_valid_url(url):
    try:
        # Makes a request to the URL and stores the response
        response = requests.get(url)

        # If the response has an OK status code (200)
        if response.status_code == 200:
            return True
        else:           
            return False
    except:
        # If any other error occurs, return False
        return False




@app.route("/", methods = ["GET", "POST"])
def home():
    form = linkForm()
    
    if request.method == "POST":
        
        if is_valid_url(request.form.get('link')):
            session['link'] = request.form.get('link')
            try:
                url = YouTube(session['link'])
                url.check_availability()
            except:
                print("url no disponible")
            return render_template("download.html", url = url, form = form)
        else:
            pass
        return redirect(url_for('home'))
    return render_template("home.html", form=form)


@app.route("/download_audio", methods = ["GET", "POST"])
def download_audio():   
    if request.method == "POST":
        buffer = BytesIO()
        url = YouTube(session['link'])
        name = url.title + '.mp3'
        audio = url.streams.get_audio_only()
        audio.stream_to_buffer(buffer)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=name)
    return redirect(url_for("home"))

@app.route("/download_video", methods = ["GET", "POST"])
def download_video():    
    # Action of the method POST 
    if request.method == "POST":
        
        # Create a buffer to save songs
        buffer = BytesIO()
        # Instantiate a Youtube object
        url = YouTube(session['link'])
        # Save song title
        name = url.title + '.mp4'
        video = url.streams.get_by_resolution(resolution="720p")
        # Send to buffer
        video.stream_to_buffer(buffer)
        # Sets the reference point at the beginning of the file 
        buffer.seek(0)
        # Download function
        return send_file(buffer, as_attachment=True, download_name=name, mimetype='video/mp4')
    return redirect(url_for("home"))



@app.route("/playlist", methods = ["GET", "POST"])
def playlist():
    form = playlistForm()
    if request.method == "POST":
        session['link'] = request.form.get('link')
        if 'list' in session['link']:
            try:
                url = Playlist(session['link'])
            except:
                flash('Link invalido', 'danger')
                return redirect('playlist')
            return render_template("playlist_download.html", url = url, form = form)
        flash('Link invalid', 'danger')
        return redirect(url_for('playlist'))
    return render_template("playlist.html", form=form)






# Function to download an individual song
def download_song(video):
    # Create a byte buffer to store the audio
    buffer = BytesIO()

    # Get song title and audio in MP3 format
    name = video.title + '.mp3'
    audio = video.streams.get_audio_only()

    # Write the audio to the buffer
    audio.stream_to_buffer(buffer)

    # Return to the beginning of the buffer
    buffer.seek(0)

    # Return the buffer as an attachment
    return buffer



@app.route("/playlist_download", methods = ["POST"])
def playlist_download():
    # Create a byte buffer to store the ZIP file
    buffer = BytesIO()

    # Create a ZIP file in the buffer
    with ZipFile(buffer, 'w') as zip:
        # If a POST request is made
        if request.method == 'POST':
            # Create a Playlist instance with the playlist URL
            playlist = Playlist(session['link'])
            
            name_playlist = playlist.title
            

            # For each video in the playlist
            for video in playlist.videos:
                # Download the song
                song = download_song(video)

                # Add the song to the ZIP file
                zip.writestr(video.title + '.mp3', song.getvalue())

    # Return to the beginning of the buffer
    buffer.seek(0)
    
    # Create a reply with the attached file
    return send_file(buffer, as_attachment=True, mimetype='application/zip', download_name=name_playlist + '.zip')



if __name__ == '__main__':
    app.run(debug=True)