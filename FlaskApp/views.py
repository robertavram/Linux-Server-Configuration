from flask import session, redirect, make_response

from handlers import GenericHandler, UploadPictureHandler
from handlers import user_required

from db_utils import dbs
from database_setup import User, Items, Images

import utils
import other_info

from flask.helpers import flash, url_for
from werkzeug.exceptions import abort


class DisconnectView(GenericHandler):

    def post(self):
        # check for csrf, verify that the state equals the form state
        if not session.get("state") == self.request.form.get('csrf'):
            flash("session state does not match the state")
            return redirect("/me")

        # check to see if there is a valid provider and route them accordingly
        provider = session.get('provider')
        if not provider:
            return self.flash_out(
                "User not logged in", 401, url_for("login_view"))
        elif provider == "google":
            return self.google.disconnect()
        elif provider == "facebook":
            return self.facebook.disconnect()
        else:
            self.auth.logout()
            return self.flash_out(
                "Credentials not valid", 401, url_for("login_view"))


class LogoutView(GenericHandler):

    def get(self):
        self.auth.logout()
        return self.flash_out("You have successfully logged out", 200, "/")


class HomeView(GenericHandler):

    def get(self):
        # get all items and the name fo their owner from the db, limit 9
        my_items = Items.get_all_w_names(dbs, limit=9)
        return self.render_template(
            "home.html", items=my_items, categories=other_info.item_categories)


class CategoryView(GenericHandler):

    def get(self, category):
        # Routing regardless of case, make category a title in order to match
        # the db
        category = category.title()

        my_items = Items.get_by_category_w_names(dbs, category)
        if my_items == False:
            return self.flash_out(
                "This category does not exist: {}".format(category), 404, url_for("home_view"))
        return self.render_template("category.html", items=my_items,
                                    my_category=category, categories=other_info.item_categories)


class ItemView(GenericHandler):

    def get(self, category, item_id):
        category = category.title()
        my_item = Items.get_by_id(dbs, item_id)
        if not my_item:
            return self.flash_out(
                "The item you are looking for does not exist", 404, "/")

        owner = User.get_by_id(dbs, my_item.user_id)

        # This really shouldn't happen but it's good to account for this
        # possibility
        if not owner:
            return self.flash_out(
                "Something went wrong, try again, if the problem persists contact us!", 500, "/")

        return self.render_template("item.html", my_category=category,
                                    owner=owner, my_item=my_item,
                                    categories=other_info.item_categories)


class LoginView(GenericHandler):

    def get(self):
        # make a new state just in case.
        session['state'] = utils.make_csrf_state(32)
        return self.render_template("login.html")


class DelUser(GenericHandler):

    @user_required
    def get(self):
        return self.render_template("delete_account.html")

    @user_required
    def post(self):
        # One can only delete themselves, if they are logged in and post with a
        # vaild state
        if not self.request.form.get("csrf") == session.get('state'):
            return self.flash_out(
                "The state does not match the session, please try again", 401, url_for("myaccount_view"))

        # Get the user id from session
        uid = session.get('uid')
        if not uid:
            self.auth.logout()
            return self.flash_out(
                "No valid login detected", 401, url_for("login_view"))

        # Revoke the access token for the provider
        provider = session.get('provider')
        if provider == "google":
            self.google.disconnect()
        elif provider == 'facebook':
            self.facebook.disconnect()

        # Delete all the items that belong to the user
        Items.delete_by_user(dbs, uid)

        # Delete the user's image
        Images.delete_by_id(dbs, self.user.picture)

        # Delete the user
        User.delete_user(dbs, uid)
        self.auth.logout()
        return self.flash_out("The account has been deleted", 200, "/")


class AuthView(GenericHandler, UploadPictureHandler):

    def callback(self, provider):
        if provider == "facebook":
            return self.facebook.connect()
        if provider == "google":
            return self.google.connect()

    def get(self, provider):
        # since some providers use get and some post for the callback
        # we allow both and route them properly
        if self.request.path.endswith("callback"):
            return self.callback(provider)
        else:
            if provider == "facebook":
                return redirect(self.facebook.first_step())
            if provider == "google":
                return redirect(self.google.first_step())
            abort(404)

    def post(self, provider):
        if self.request.path.endswith("callback"):
            return self.callback(provider)
        abort(404)


class ItemAddView(GenericHandler, UploadPictureHandler):

    @user_required
    def get(self):
        return self.render_template(
            "add_item.html", categories=other_info.item_categories)

    @user_required
    def post(self):
        # check for csrf
        if not self.request.form.get("state") == session['state']:
            return self.flash_out(
                "The state did not match your session, please try again", 401, "/")

        # Define the available variables to populate the object
        my_vars = ['name', 'category', 'description', 'link']
        # Define which ones should be Title case
        titles = ['name', 'category']
        new_item = {}

        for mp in my_vars:
            if mp in titles:
                new_item[mp] = self.request.form.get(mp).title()
            else:
                new_item[mp] = self.request.form.get(mp)

        new_item['user_id'] = self.user_info['uid']

        # this test excludes the optional image file test
        new_item_valid, new_item_test_error = utils.test_new_item(new_item)
        if not new_item_valid:
            # Here we should really re-populate the fields with the content submitted
            # for now one has to resubmit, there should also be a test on the
            # front end
            return self.flash_out(
                new_item_test_error, 401, url_for("additem_view"))

        # Check to see if this potential item is already in the db
        if Items.item_exists(dbs, new_item['name'], new_item['category']):
            return self.flash_out(
                "This Item already exists in this category", 401, url_for("additem_view"))

        # Check to see if there is a picture submission and upload it
        upload_file = self.request.files["picture"]
        if upload_file:
            image_name = utils.remove_special_characters(
                new_item["name"] + new_item["category"]) + "_img"
            img = self.upload_image_file(upload_file, image_name)
            # if the upload and storage succeeds add the img id to the item.
            if img:
                new_item['picture'] = img.id

        # add the new item to the database
        Items.addItem(dbs, new_item)

        return self.flash_out("New Item added", 200, "/")


class ItemDeleteView(GenericHandler):

    @user_required
    def get(self, category, item_id):
        my_item = Items.get_by_id(dbs, item_id)
        if not my_item or my_item.user_id != self.user_info['uid']:
            return self.flash_out(
                "The item you are looking for does not exist or you are not allowed to delete it", 401, "/")
        return self.render_template(
            "item_delete.html", my_item=my_item, my_category=category)

    @user_required
    def post(self, category, item_id):
        state = self.request.form.get("csrf")

        if state != session['state']:
            return self.flash_out(
                "The CSRF state is not valid, try again", 401, "/")

        item = Items.get_by_id(dbs, item_id)
        if not item or item.user_id != self.user_info['uid']:
            return self.flash_out(
                "The item you are trying to delete does not belong to you or this item was already deleted.", 401, "/")

        result = Items.delete_by_item(dbs, item)
        if not result:
            return self.flash_out(
                "The item you are trying to delete does not exist", 401, "/")

        return self.flash_out("Your item was deleted successfully", 200, "/")


class ItemUpdateView(GenericHandler, UploadPictureHandler):

    @user_required
    def get(self, category, item_id):
        my_item = Items.get_by_id(dbs, item_id)
        # Check if the item requested is in the db or if it belongs to the
        # session user
        if not my_item or my_item.user_id != self.user_info['uid']:
            return self.flash_out(
                "The item you are looking for does not exist or you are not allowed to delete it", 401, "/")

        return self.render_template("item_update.html", my_item=my_item,
                                    my_category=category, categories=other_info.item_categories)

    @user_required
    def post(self, category, item_id):
        # Check CSRF state
        state = self.request.form.get("csrf")
        if state != session['state']:
            return self.flash_out(
                "The CSRF state is not valid, try again", 401, "/")

        # Check if item is in the db
        item = Items.get_by_id(dbs, item_id)
        if not item or item.user_id != self.user_info['uid']:
            return self.flash_out(
                "The item you are trying to update does not belong to you.", 401, "/")

        # List of fileds allowed to be updated
        update_fields = ["name", "description", "category", "link"]
        new_vals = {}
        for field in update_fields:
            new_val = self.request.form.get(field)
            # if the user is choosing to update this field and it's not the
            # same value as before
            if new_val and not getattr(item, field) == new_val:
                new_vals[field] = new_val
                setattr(item, field, new_val)

        # if there are updates and they are valid properties
        if new_vals:
            new_vals_valid, new_vals_test_error = utils.test_item_prop(
                new_vals)
            if not new_vals_valid:
                return self.flash_out(new_vals_test_error, 401, "/")

        prev_img_id = None
        upload_file = self.request.files["picture"]
        if upload_file:
            if item.picture:
                # Changing the image name in order to prevent atomicity
                # problems (deleting and immediately writing to the same id)
                image_name = item.picture.split(".")[0]
                image_number = (
                    (int(image_name[-1]) + 1) if image_name[-1].isdigit() else 1)
                image_name = image_name + str(image_number)
            else:
                image_name = utils.remove_special_characters(
                    item.name + item.category) + "_img"
            img = self.upload_image_file(upload_file, image_name)
            if img:
                prev_img_id = item.picture
                item.picture = img.id

        # if there are no new values and no new image
        elif not new_vals:
            return self.flash_out(" No new updates submitted", 200, url_for(
                "item_view", category=item.category, item_id=item.id))

        # persist the changes
        Items.update_item(dbs, item)

        # Erase the previous picture from the db
        if prev_img_id:
            Images.delete_by_id(dbs, prev_img_id)

        return self.flash_out("Item has been updated", 200, url_for(
            "item_view", category=item.category, item_id=item.id))


class MyAccountView(GenericHandler):

    @user_required
    def get(self):
        return self.render_template(
            "myaccount.html", me=self.user, provider=session.get("provider").title())


class ShowPictureView(GenericHandler):

    def get(self, pid):
        # Get picture from db
        picture = dbs.query(Images).get(pid)
        if not picture:
            abort(404)
        picture = picture.data
        picture_format = pid.split(".")[1]
        response = make_response(picture)
        # Add proper header for serving it
        response.headers['Content-Type'] = 'image/' + picture_format
        return response


class UserView(GenericHandler):

    def get(self, uid):
        my_user = User.get_by_id(dbs, uid)
        if not my_user:
            return self.flash_out("No user found", 404, "/")
        user_items = Items.get_all_by_user(dbs, uid)
        for item in user_items:
            item.uname = my_user.name
        return self.render_template(
            "user_view.html", my_user=my_user, items=user_items)
