import random
import string
import other_info
import re
from dicttoxml import dicttoxml


def make_csrf_state(size):
    ''' Makes a CSRF state by randomly choosing uppercase letters and digits '''
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in xrange(size))

def valid_item_name(item_name):
    ''' Test item name for bad words or format etc
        -not fully implemented for this project'''
    if len(item_name) > 50:
        return False;
    
    return True

def valid_item_description(item_description):
    '''test item description for bad words or format etc
    -not fully implemented for this project'''
    if len(item_description) > 1000:
        return False
    return True

def allowed_file(filename):
    ''' Checks if an image file has the right extension '''
    ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'gif', "png"])
    
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
        
def valid_link(link):
    ''' Checks if the link provided is a valid link format 
    - not fully implemented for this project'''
    pat = re.compile("/^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/")
    pat.match(link)
    if not pat:
        return False
    return True if link else False

def test_new_item(item_dict):
    ''' takes an item dictionary and checks if all fields are properly filled
    returns: tuple (Bool: Success, string: Error) '''
    # for now just test the surface things
    category = item_dict.get("category")
    if not category in other_info.item_categories:
        return (False, "Category is invalid")
    name = item_dict.get("name")
    if not name or not valid_item_name(name) == True:
        return (False, "Name not valid")
    description = item_dict.get("description")
    if not valid_item_description(description) == True:
        return (False, "Description not valid")
    link = item_dict.get("link")
    if link and not valid_link(item_dict["link"]):
        return (False, "Link is not valid")
    return (True, None)

def test_item_prop(item_dict):
    ''' Tests all the properties passed in the item_dict 
    and checks if they are valid for updating the item '''
    my_valid_vars = ['name', 'category', 'description', 'link']
    for kw in item_dict:
        if kw not in my_valid_vars:
            return (False, "You are trying to update a property that doesn't exist: %s"%kw)
        if kw == 'name' and not valid_item_name(item_dict[kw]):
            return (False, "Name not valid")
        if kw == 'description' and not valid_item_description(item_dict[kw]):
            return (False, "Description not valid")
        if kw == 'category' and item_dict[kw] not in other_info.item_categories:
            return (False, "Category not valid")
        if kw == 'link' and not valid_link(item_dict[kw]):
            return (False, "Link not valid")
    return (True, None)

def remove_special_characters(my_string):
    return ''.join(e for e in my_string if e.isalnum()).lower()

def get_cat_regex():
    return "(?i)"+'|'.join(other_info.item_categories)

def makexml(my_dict):
    return dicttoxml(my_dict)
        