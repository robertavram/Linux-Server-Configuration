from flask import Flask

from werkzeug.routing import BaseConverter

from views import HomeView, DelUser, LoginView,\
    LogoutView, ShowPictureView, CategoryView,\
    DisconnectView, AuthView, ItemDeleteView,\
    ItemAddView, ItemUpdateView, ItemView, MyAccountView, UserView

import utils

app = Flask(__name__)
app.config.from_object('config_settings.Testing')

# Adds functions to be available in the jinja env
app.jinja_env.globals.update(strip_alnum=utils.remove_special_characters)


class RegexConverter(BaseConverter):

    '''Sets up regex to be used in the add_url_rule '''

    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter


app.add_url_rule("/", view_func=HomeView.as_view('home_view'))
app.add_url_rule("/json", view_func=HomeView.as_view('home_json'))
app.add_url_rule("/xml", view_func=HomeView.as_view('home_xml'))
# /category
app.add_url_rule('/<regex("{}"):category>'.format(utils.get_cat_regex()),
                 view_func=CategoryView.as_view('category_view'))
app.add_url_rule(
    '/<regex("{}"):category>/json'.format(
        utils.get_cat_regex()),
    view_func=CategoryView.as_view('category_json'))
app.add_url_rule(
    '/<regex("{}"):category>/xml'.format(
        utils.get_cat_regex()),
    view_func=CategoryView.as_view('category_xml'))
# /category/item_id
app.add_url_rule('/<regex("{}"):category>'.format(utils.get_cat_regex()) +
                 '/<int:item_id>', view_func=ItemView.as_view('item_view'))
app.add_url_rule('/<regex("{}"):category>'.format(utils.get_cat_regex()) +
                 '/<int:item_id>/json', view_func=ItemView.as_view('item_json'))
app.add_url_rule('/<regex("{}"):category>'.format(utils.get_cat_regex()) +
                 '/<int:item_id>/xml', view_func=ItemView.as_view('item_xml'))
# /category/item_id/delete
app.add_url_rule('/<regex("{}"):category>'.format(utils.get_cat_regex()) +
                 '/<int:item_id>/delete', view_func=ItemDeleteView.as_view('itemdelete_view'))
# /category/item_id/update
app.add_url_rule('/<regex("{}"):category>'.format(utils.get_cat_regex()) +
                 '/<int:item_id>/update', view_func=ItemUpdateView.as_view('itemupdate_view'))
app.add_url_rule("/me", view_func=MyAccountView.as_view('myaccount_view'))
app.add_url_rule("/items/add", view_func=ItemAddView.as_view('additem_view'))

app.add_url_rule("/user/<int:uid>", view_func=UserView.as_view('user_view'))

# /img/image.jpg - serves images from the db
app.add_url_rule(
    "/img/<pid>",
    view_func=ShowPictureView.as_view('showpicture_view'))

# delete current user - deletes their items as well
app.add_url_rule("/delete", view_func=DelUser.as_view('deleteuser_view'))
app.add_url_rule("/login", view_func=LoginView.as_view('login_view'))
app.add_url_rule("/logout", view_func=LogoutView.as_view('logout_view'))

app.add_url_rule(
    "/disconnect",
    view_func=DisconnectView.as_view('disconnect_view'))

# auth
app.add_url_rule('/auth/<provider>', view_func=AuthView.as_view("auth_first"))
app.add_url_rule(
    '/auth/<provider>/callback',
    'auth_callback',
    view_func=AuthView.as_view("auth_callback"))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
