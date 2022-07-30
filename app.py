import sys
import json
import dateutil.parser
import babel
import collections
import collections.abc
collections.Callable = collections.abc.Callable
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
from models import db, Venue,Artist, Show
import config

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__, template_folder = 'templates')
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#----------------------------------------------------------------------------#
#  Venues
#  --------------------------------------------------------------------------#

@app.route('/venues')
def venues():
  venues = Venue.query.all()
  data = []
  locations = set()

  for venue in venues:
    locations.add((venue.city, venue.state))

  for location in locations:
    data.append({
        "city": location[0],
        "state": location[1],
        "venues": []
    })

  for venue in venues:
    num_upcoming_shows = 0

    shows = Show.query.filter_by(venue_id=venue.id).all()
    current_date = datetime.now()

    for show in shows:
      if show.start_time > current_date:
        num_upcoming_shows += 1
    

    for venue_location in data:
      if venue.state == venue_location['state'] and venue.city == venue_location['city']:
        venue_location['venues'].append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": num_upcoming_shows
        })
  return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term=request.form.get('search_term', '')
  results = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  response = {
    "count": len(results),
    "data": results
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  shows = Show.query.filter_by(venue_id=venue_id).all()
  data = {}
  prev_shows = []
  upcoming_shows = []
  current_time = datetime.now()

  for show in shows:
    data = {
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time))
    }
    if show.start_time > current_time:
      upcoming_shows.append(data)
    else:
      prev_shows.append(data)

  data = {
    "id": venue.id,
    "name": venue.name,
    "city": venue.city,
    "state": venue.state,
    "address": venue.address,
    "phone": venue.phone,
    "genres": venue.genres,
    "facebook_link": venue.facebook_link,
    "image_link": venue.image_link,
    "website_link": venue.website_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "prev_shows": prev_shows,
    "upcoming_shows": upcoming_shows,
    "prev_shows_count": len(prev_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_venue.html', venue=data)
  
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  venue = Venue(
    name=form.name.data, 
    city=form.city.data, 
    state=form.state.data, 
    address=form.address.data,
    phone=form.phone.data, 
    genres=form.genres.data,
    facebook_link=form.facebook_link.data, 
    image_link=form.image_link.data, 
    website_link=form.website_link.data, 
    seeking_talent=form.seeking_talent.data,
    seeking_description=form.seeking_description.data
  )
  try:
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue'+ request.form['name'] + ' could not be listed')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  venue = {
    "id": venue_id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website_link": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)
  venue = Venue.query.get(venue_id)
  new_venue = dict(
    name = form.name.data,
    city = form.city.data,
    state = form.state.data,
    phone = form.phone.data,
    address = form.address.data,
    genres = form.genres.data,
    facebook_link = form.facebook_link.data,
    image_link = form.image_link.data,
    website_link = form.website_link.data,
    seeking_talent = form.seeking_talent.data,
    seeking_description = form.seeking_description.data
  )
  try:
    db.session.query(Venue).filter(Venue.id==venue_id).update(new_venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' has been updated')
  except:
    db.session.rollback()
    flash('An error occured while trying to update venue')
  finally:
    db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

@app.route('/venues/<venue_id>/delete', methods=['POST']) 
def delete_venue(venue_id):
  venue = Venue.query.get_or_404(venue_id)
  venue_name = venue.name
  try:
    current_session = db.object_session(venue)
    current_session.delete(venue)
    current_session.commit()
    flash('Venue ' + venue_name + ' was deleted.')
  except:
    flash('An error occured and Venue ' + venue_name + ' was not deleted')
    current_session.rollback()
  finally:
    current_session.close()
  return redirect(url_for('venues'))

#----------------------------------------------------------------------------#
#  Artists
#----------------------------------------------------------------------------#

@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term=request.form.get('search_term', '')
  results = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  response = {
    "count": len(results),
    "data": results
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  shows = Show.query.filter_by(artist_id=artist_id).all()
  data ={}
  prev_shows = []
  upcoming_shows = []
  current_time = datetime.now()

  for show in shows:
    data = {
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": format_datetime(str(show.start_time))
    }
    if show.start_time > current_time:
      upcoming_shows.append(data)
    else:
      prev_shows.append(data)

  data = {
    "id": artist.id,
    "name": artist.name,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "genres": artist.genres,
    "facebook_link": artist.facebook_link,
    "image_link": artist.image_link,
    "website_link": artist.website_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "prev_shows": prev_shows,
    "upcoming_shows": upcoming_shows,
    "prev_shows_count": len(prev_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_artist.html', artist=data)


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm()
  artist = Artist(
    name = form.name.data,
    city = form.city.data,
    state = form.state.data,
    phone = form.phone.data,
    genres = form.genres.data,
    facebook_link = form.facebook_link.data,
    image_link = form.image_link.data,
    website_link = form.website_link.data,
    seeking_venue = form.seeking_venue.data,
    seeking_description = form.seeking_description.data
  )
  try:
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error ocurred. Artist ' + request.form['name'] + ' could not be listed')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  artist_data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "facebook_link": artist.facebook_link,
    "image_link": artist.image_link,
    "website_link": artist.website_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description
  }
  return render_template('forms/edit_artist.html', form=form, artist=artist_data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
  artist = Artist.query.get(artist_id)
  new_artist = dict(
    name = form.name.data,
    city = form.city.data,
    state = form.state.data,
    phone = form.phone.data,
    genres = form.genres.data,
    facebook_link = form.facebook_link.data,
    image_link = form.image_link.data,
    website_link = form.website_link.data,
    seeking_venue = form.seeking_venue.data,
    seeking_description = form.seeking_description.data
  )
  try:
    db.session.query(Artist).filter(Artist.id==artist_id).update(new_artist)
    db.session.commit()
    flash('The Artist ' + request.form['name'] + ' has been successfully updated!')
  except:
    db.session.rollback()
    flash('An error occured while trying to update artist')
  finally:
    db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/artist/<artist_id>', methods=['POST']) 
def delete_artist(artist_id):
  artist = Artist.query.get_or_404(artist_id)
  artist_name = artist.name
  try:
    current_session = db.object_session(artist)
    current_session.delete(artist)
    current_session.commit()
    flash('Artist ' + artist_name + ' was deleted.')
  except:
    flash('an error occured and Artist ' + artist_name + ' was not deleted')
    current_session.rollback()
  finally:
    current_session.close()

  return redirect(url_for('artists'))

#----------------------------------------------------------------------------#
#  Shows
#----------------------------------------------------------------------------#

@app.route('/shows')
def shows():
  shows = Show.query.order_by(db.desc(Show.start_time))
  data = []
  for show in shows:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time))
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create', methods=['GET'])
def create_shows():
  form = ShowForm(request.form)
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)
  new_show = Show()
  new_show.artist_id = request.form['artist_id']
  new_show.venue_id = request.form['venue_id']
  new_show.start_time = request.form['start_time']
  try:
    db.session.add(new_show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

'''