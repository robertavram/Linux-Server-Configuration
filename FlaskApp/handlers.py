from flask import request, session, redirect, render_template, make_response, flash
from flask.views import MethodView
import secret_keys as secrets

from oauth2client.client import OAuth2Credentials
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

import requests
import time


import json
import utils
import urllib

from db_utils import dbs
from database_setup import User, Items, Images
from werkzeug.utils import cached_property

import imghdr
from PIL import Image, ImageOps
from StringIO import StringIO

from datetime import datetime
from other_info import app_files

class MyEncoder(json.JSONEncoder):

    ''' Json encoder, helps with encoding objects '''

    def default(self, obj):

        # If the object to be encoded is User or Items return their serialized
        # form
        if isinstance(obj, User) or isinstance(obj, Items):
            return obj.serialize
        if isinstance(obj, datetime):
            return obj.isoformat()

        return json.JSONEncoder.default(self, obj)


def user_required(handler):
    """
        Decorator that checks if there's a user associated with the current session.
        Will also fail if there's no session present.
    """

    def check_login(self, *args, **kwargs):
        # Make sure there is a provider and credentials stored in session
        provider = session.get('provider')
        credentials = session.get('credentials')
        if not credentials or not provider:
            return redirect("/login")

        # check if there is a user
        if not self.user:
            return redirect("/login")

        return handler(self, *args, **kwargs)

    return check_login


class GoogleOauth(object):

    ''' This class is meant to be inherited by the Oauth class - it makes it easier to read and understand
        It uses functions that are available only if its used as a parent of Oauth, Auth, GenericHandler '''

    def first_step(self):
        '''
            returns the redirect url for the user to authorize us with google
        '''
        # Check the CSRF state
        if self.request.args.get('state') != session['state']:
            return self.flash_out("Invalid state", 401)

        # Create auth flow from client secrets
        oauth_flow = flow_from_clientsecrets(
            '{}client_secrets.json'.format(app_files),
            scope='profile email')
        oauth_flow.redirect_uri = secrets.GOOGLE_REDIRECT_URI

        params = {
            "scope": "https://www.googleapis.com/auth/plus.profile.emails.read",
            "client_id": oauth_flow.client_id,
            "redirect_uri": oauth_flow.redirect_uri,
            'response_type': 'code',
            'state': session['state']
        }
        return oauth_flow.auth_uri + "?" + urllib.urlencode(params)

    def connect(self):
        ''' intended for google callback, either logs in a existing user or creates a new user and logs them in '''

        code = self.request.args.get('code')
        print "received code of %s " % code

        try:
            # Upgrade the authorization code into a credentials object
            oauth_flow = flow_from_clientsecrets(
                '{}client_secrets.json'.format(app_files),
                scope='profile email')
            oauth_flow.redirect_uri = secrets.GOOGLE_REDIRECT_URI
            credentials = oauth_flow.step2_exchange(code)

        except FlowExchangeError as e:
            print e
            return self.flash_out(
                "Failed to upgrade the authorization code.", 401)

        stored_credentials = session.get('credentials')
        stored_gplus_id = session.get('pid')

        # Store the access token in the session for later use, maybe in another
        # version
        session['provider'] = 'google'
        session['credentials'] = credentials.to_json()
        # pid stands for provider id
        session['pid'] = credentials.id_token['sub']

        if stored_credentials and (
                credentials.id_token['sub'] == stored_gplus_id):
            return self.flash_out('Current user is already logged in.')

        print "#Geting google user info"
        # Get user info
        u_info = self.google.get_user_info(
            credentials.access_token,
            credentials.id_token['sub'])

        if u_info.get("error"):
            self.auth.logout()
            return self.flash_out(
                "Something went wrong with the user_info retrieval", 401)

        my_image = self.upload_image_link(u_info['image']['url'][:-2] + '200',
                                          utils.remove_special_characters(u_info['displayName'] + u_info['id'] + 'google'))
        # retrieve an existing user or store a new user in the db
        my_user = self.auth.store_user(u_info['displayName'],
                                       u_info["emails"][0]['value'],
                                       "/img/" + my_image.id)[1]

        if not my_user:
            self.auth.logout()
            return self.flash_out("Could not store the user to the db")

        # store the user id and the user name in session
        session['uid'] = my_user.id
        session['name'] = my_user.name

        return redirect("/")

    def disconnect(self):
        ''' revokes the access token from google and logs user out'''
        # get the credentials from session
        credentials = session.get('credentials')

        if credentials:
            credentials = json.loads(credentials)
        else:
            # We clear login credentials from session for good measure
            self.auth.logout()
            return self.flash_out("no user logged in")

        # url for revoking tokens
        url = 'https://accounts.google.com/o/oauth2/revoke'
        result = requests.get(
            url, params={
                "token": credentials['access_token']})
        if result.status_code == 200:
            self.auth.logout()
            return self.flash_out('great success')
        else:
            self.auth.logout()
            return self.flash_out(
                'token expired or revoked, could not revoke token provided', 401)

    def get_user_info(self, gtoken, userid):
        ''' Returns the user info based on provided token and google userid '''

        userinfo_url = "https://www.googleapis.com/plus/v1/people/{}".format(
            userid)
        params = {'access_token': gtoken, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)
        return answer.json()

    def check_session_token(self, fullcheck=False):
        ''' Gets the token from the session and checks its validity (locally),
            if fullcheck is True, it sends a server request to google to check if it was revoked
            Returns: (bool: Valid, string: Error)'''

        if session.get("provider") == "google":
            # Create oauth2credentials object form json stored in session
            credentials = OAuth2Credentials.from_json(
                session.get('credentials'))
        else:
            return (False, "No provider or provider not google")
        if not credentials:
            return (False, "No credentials or credentials not valid")

        if credentials.access_token_expired:
            return (False, "Token Expired")

        if fullcheck:
            token_check_result = self.google.check_token(
                credentials.access_token,
                session.get("pid"))  # @UndefinedVariable
            if not token_check_result[0]:
                return (
                    False, "Token check on server failed: " + token_check_result[1])

        return (True, None)

    def renew_session_token(self):
        ''' Not implemented for current version of the app because there are no server-side apis called
         outside of user info on login'''
        pass

    def check_token(self, gtoken, gplus_id):
        ''' Checks if a token is still valid by sending a request to the google servers
            Also checks if the token was granted token belongs to the user in question and to our app
            Takes in: token, google plus id,
            Returns (bool: Valid, string: Error) '''
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
               % gtoken)
        result = requests.get(url=url)
        result = result.json()

        if result.get('error'):
            return (False, result['error'])

        if result['user_id'] != gplus_id:
            return (False, "User Id does not match the token UserID")

        if result['audience'] != secrets.GOOGLE_APP_ID:
            return (False, "Token's client ID does not match app's.")

        return (True, None)


class FacebookOauth(object):

    ''' This class is meant to be inherited by the Oauth class - it makes it easier to read and understand
        It uses functions that are available only if its used as a parent of Oauth, Auth, GenericHandler '''

    def first_step(self):
        '''
            returns the redirect url for the user to authorize us with facebook
        '''
        # Checking CSRF state
        if request.args.get('state') != session['state']:
            return self.json_out("invalid state", 401)

        params = {"client_id": secrets.FB_APP_ID,
                  "redirect_uri": secrets.FB_REDIRECT_URI,
                  "state": session['state'],
                  "scope": "public_profile, email"}
        url = "https://www.facebook.com/dialog/oauth?" + \
            urllib.urlencode(params)
        return url

    def connect(self):
        ''' intended for facebook callback, either logs in a existing user or creates a new user and logs them in '''
        if request.args.get('state') != session['state']:
            return self.json_out("invalid state", 401)

        # get the authorization code
        code = request.args.get('code')

        # Get the access token for this user
        url = "https://graph.facebook.com/v2.3/oauth/access_token"
        params = {"client_id": secrets.FB_APP_ID,
                  "redirect_uri": secrets.FB_REDIRECT_URI,
                  "client_secret": secrets.FB_APP_SECRET,
                  "code": code}
        answer = requests.get(url, params=params)
        token_answer = answer.json()

        # check if the exchange succeeded
        if token_answer.get("error"):
            return self.flash_out("could not make the exchange", 401)

        # Get user info
        u_inf = self.oauth.facebook.get_user_info(token_answer['access_token'])

        # check if the user info request succeeded
        if u_inf.get("error"):
            return self.json_out("authentication failed", 401)

        # Try to find the user in the db
        user = self.auth.get_user_by_email(u_inf['email'])
        if not user:
            # get user picture before we store user
            u_pic = requests.get("https://graph.facebook.com/v2.2/me/picture", params={"access_token": token_answer['access_token'],
                                                                                       "redirect": 0,
                                                                                       "width": 200,
                                                                                       "height": 200}).json()
            # if request for picture fails put a default avatar as a picture
            if u_pic.get("error"):
                user = self.auth.store_user(
                    name=u_inf["name"],
                    email=u_inf['email'],
                    picture='/static/img/default_avatar.jpg')
            else:
                picture = self.upload_image_link(
                    u_pic['data']['url'],
                    utils.remove_special_characters(
                        u_inf["id"] +
                        u_inf["name"] +
                        "facebook"))
                # Store the new user in the db
                user = self.auth.store_user(
                    name=u_inf["name"],
                    email=u_inf['email'],
                    picture="/img/" +
                    picture.id)[1]

            # If storing it in the db doesn't work, logout and throw an error
            if not user:
                self.auth.logout()
                return self.flash_out("could not store user in the db", 401)

        # Set credentials to the received token
        credentials = token_answer
        # Calculate the token expiration time based on the server time
        # and store it for easy token expiration check
        credentials['expiration'] = int(
            time.time() +
            token_answer['expires_in'])
        self.auth.set_login(user, credentials, "facebook", u_inf['id'])

        return redirect("/")

    def get_user_info(self, access_token):
        ''' Returns user info based on the received facebook token '''
        userinfo_url = 'https://graph.facebook.com/v2.3/me'
        answer = requests.get(
            userinfo_url,
            params={
                "access_token": access_token})
        return answer.json()

    def disconnect(self):
        ''' revokes the access token from facebook and logs user out'''

        facebook_id = session.get("pid")
        access_token = session['credentials'][
            'access_token'] if session.get('credentials') else None
        # Check if the facebook id and the access token are present in the
        # session
        if not (facebook_id and access_token):
            self.auth.logout()
            return self.flash_out("no user is logged in")

        # Shoot a request to facebook to revoke the token and disconnect the
        # user
        url = 'https://graph.facebook.com/%s/permissions' % facebook_id
        result = requests.delete(url, params={"access_token": access_token})

        if result.status_code == 200:
            self.auth.logout()
            return self.flash_out("great success")
        else:
            return self.flash_out("something went wrong")

    def check_session_token(self, fullcheck=False):
        ''' Gets the token from the session and checks its validity (locally),
            if fullcheck is True, it sends a server request to facebook to check if it was revoked
            Returns: (bool: Valid, string: Error)'''

        credentials = session.get("credentials")
        provider = session.get("provider")
        if provider != "facebook" or not credentials:
            return (False, "No valid credentials present")

        if (credentials['expiration'] < time.time()):
            return (False, "Token Expired")

        if fullcheck:
            return self.oauth.facebook.check_token(
                credentials['access_token'], session.get("pid"))

        return (True, None)

    def get_app_token(self):
        ''' function that asks facebook for an app token. This is useful for making api calls offline,
            this function is not used in the current version of the app '''
        params = {"client_id": secrets.FB_APP_ID,
                  "client_secret": secrets.FB_APP_SECRET,
                  "grant_type": "client_credentials"}

        url = "https://graph.facebook.com/oauth/access_token"
        app_token = requests.get(url, params=params)

        if app_token.status_code != 200:
            return None
        # the request returns the token in the body
        # this is to return only the token without 'access_token:'(13 char)
        return app_token.text[13:]

    def check_token(self, token, pid):
        ''' Checks if a token is still valid by sending a request to the facebook servers
            Also checks if the token was granted token belongs to the user in question and to our app
            Takes in: token, facebook id,
            Returns (bool: Valid, string: Error) '''

        url = "https://graph.facebook.com/debug_token"
        params = {"input_token": token,
                  "access_token": self.auth.facebook.get_app_token()}
        token_response = requests.get(url, params=params).json()

        if token_response.get("error"):
            return (False, token_response['error'])
        if not token_response['data']["is_valid"]:
            return (False, "token not valid")
        if token_response['data']['user_id'] != pid:
            return (False, "token does not belong to this user")

        return (True, None)


class OAuthHandler(GoogleOauth, FacebookOauth):

    ''' Class designed just for structure and readability
    eg: calling: self.google.connect() and self.facebook.connect() will access the proper functions within google and facebook
    This class is meant to be inhereted by Auth class, and it can be expanded to contain other ouath providers as well'''
    @cached_property
    def google(self):
        ''' Makes it so one can call self.google.googlefunction, and takes advantage of the lazy-loading'''
        return super(OAuthHandler, self)

    @cached_property
    def facebook(self):
        ''' Makes it so one can call self.facebook.facebookfunction, and takes advantage of the lazy-loading'''
        return super(GoogleOauth, self)


class Auth(OAuthHandler):

    ''' Class designed just for structure and readability
        Deals with auth related issues, it is meant to be inherited by GenericHandler and addressed as self.auth'''

    @cached_property
    def oauth(self):
        ''' Makes it so one can refer to all the auth providers under self.oauth.google,
        to help with readability and takes advantage of @cached-property lazy-loading'''
        return super(Auth, self)

    def get_user_by_email(self, email):
        ''' Takes and email and checks the DB for the user,'''

        return User.get_by_email(dbs, email)

    def store_user(
            self, name, email, picture="/static/img/default_avatar.jpg"):
        '''This function stores the user if there isn't a user with the same email in the DB,
        it helps if a user uses multiple oauth providers to log into the app,
        it makes it so that the user has only one account and can still edit their own info
        Takes in: Name, email, picture
        Returns (Bool: Success, User - if present in the db or just storred)'''
        # Make sure there is no user with the same credentials
        my_user = self.get_user_by_email(email)
        if my_user:
            return (False, my_user)
        try:
            my_user = User(name=name, email=email, picture=picture)
            dbs.add(my_user)
            dbs.commit()
        except:
            return(False, None)

        return (True, my_user)

    def get_user_by_session(self):
        ''' Returns the session user, by querying the db for the user id found in session '''
        uid = session.get("uid")
        if not uid:
            return None
        myuser = User.get_by_id(dbs, uid)
        if not myuser:
            return None
        return myuser

    def get_session_user(self):
        ''' Returns the user info stored in session, putting it in a dict type,
        if no user present, returns None '''
        u = {}
        u['uid'] = session.get('uid')
        u['name'] = session.get('name')
        if not(u['uid'] and u['name']):
            return None
        return u

    def set_login(self, user, credentials, provider, pid):
        ''' stores provided credentials in session '''
        session['credentials'] = credentials
        session['name'] = user.name
        session['pid'] = pid
        session['uid'] = user.id
        session['provider'] = provider

    def logout(self):
        ''' Erases all the credentials from session '''
        my_vars = ['credentials', 'uid', 'name', 'provider', 'pid']
        for mv in my_vars:
            try:
                del session[mv]
            except:
                pass

    def clear_session(self):
        ''' Clears everything in session '''
        session.clear()


class GenericHandler(Auth, MethodView):

    ''' Main Handler to be inherited by a View class '''

    def __init__(self):
        self.request = request

    @cached_property
    def auth(self):
        return super(GenericHandler, self)

    @cached_property
    def user_info(self):
        ''' Returns a dict with the user credentials present in session '''
        return self.auth.get_session_user()

    @cached_property
    def user(self):
        ''' Returns User or None,
        returns the User instance based on the user credentials stored in session '''
        u = self.user_info
        if not u:
            return None
        return self.auth.get_user_by_session()

    def flash_out(self, message, response_type=200, redirect_to="/"):
        ''' Returns either a flash message and redirects to the proper page,
         or if it's a json request it returns json'''
        if self.request.path.endswith("/json"):
            return self.json_out(message, response_type)
        else:
            errors = {200: "alert-success",
                      401: "alert-warning",
                      404: "alert-warning",
                      500: "alert-danger"}
            flash(message, errors[response_type])
            return redirect(redirect_to)
        return self.json_out(message, response_type)

    def render_template(self, template, **kw):
        ''' Renders a template or creates a json response if needed '''
        if self.request.path.endswith("/json"):
            return self.json_out(kw, 200)
        if self.request.path.endswith("/xml"):
            return self.xml_out(kw, 200)

        kw['user_info'] = self.user_info
        # check if there is a state in the session and store a new one if not
        if not session.get("state"):
            session['state'] = utils.make_csrf_state(30)
        kw['state'] = session['state']
        return render_template(template, **kw)

    def json_out(self, message, response_type=200):
        ''' Returns a JSON response '''
        response = make_response(
            json.dumps(
                message,
                cls=MyEncoder),
            response_type)
        response.headers['Content-Type'] = 'application/json'
        return response

    def xml_out(self, message, response_type=200):
        ''' Returns an XML response '''
        new_message = {}
        for kw in message:
            if isinstance(message[kw], User) or isinstance(message[kw], Items):
                new_message[kw] = message[kw].serialize
            else:
                new_message[kw] = message[kw]

        myxml = utils.makexml(new_message)
        response = make_response(myxml, response_type)
        response.headers['Content-Type'] = 'application/xml'
        return response


class UploadPictureHandler(object):

    ''' Handles the pciture uploading process '''

    def store_image(self, im, img_format, image_name, fit_size=(128, 128)):
        ''' Takes in: im : PIL image object,
                      img_format: the image format,
                      image_name: the name under which the image will be stored in the DB '''
        image_name = image_name + "." + img_format
        # Make the image fit in a 128 by 128 square
        im = ImageOps.fit(im, fit_size, Image.ANTIALIAS)
        # Create a String IO file
        f = StringIO()
        # Save the image to f
        im.save(f, img_format)
        # Store the StringIO in a blob in Images
        my_img = Images.store_img(dbs, image_name, f.getvalue())
        return my_img

    def upload_image_file(self, upload_file, image_name):
        ''' takes an uploaded file and stores it under image_name in Images '''
        image_data = upload_file.read()
        # Check if the file received is actually an image
        img_format = self.valid_image(image_data)
        if img_format:
            # Create a PIL Image object
            im = Image.open(StringIO(image_data))
            return self.store_image(im, img_format, image_name)
        else:
            return None

    def upload_image_link(self, link, image_name):
        ''' takes a link of an image and stores the image under image_name '''
        response = requests.get(link)
        # Check if the content in the link is actually an image
        img_format = self.valid_image(response.content)
        if img_format:
            im = Image.open(StringIO(response.content))
            del response
            return self.store_image(
                im, img_format, image_name, fit_size=(200, 200))
        else:
            return None

    def valid_image(self, image_data):
        acceptable_formats = ['jpg', 'jpeg', 'png', "gif"]
        img_format = imghdr.what("upload_file", image_data)
        if img_format in acceptable_formats:
            return img_format
        return False
