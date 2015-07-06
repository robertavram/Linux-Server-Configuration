#[FlutterHub]

FlutterHub is a flask web application that allows users to post a summary of a fashion blog post with a link.
FlutterHub uses a database (with the help of an ORM -> SqlAlchemy) to store these posts under a specified list of categories.
It uses Oauth2 to authenticate users and creates user accounts based on the information received from the oauth providers (in this case Google and Facebook).
Posts can contain pictures that get processed and stored in the database.
FlutterHub also exposes json and xml endpoints.

Because I was sitting on a domain name, :) until it expires flutterhub runs as an example at:
http://www.flutterhub.com


####Instalation Guide - Vagrant:
  - you should have [virtual-box] and [vagrant] installed
  - copy the application files in the desired folder and run vagrant up, vagrant ssh respectively
  - run 
	```
	 $ python /vagrant/application.py
	```

####Instalation Guide - Docker:
  - you should have [Docker] installed and navigate to the app directory where the Dockerfile resides.
  - run 
        ```$ docker build -t [yourdockerimagename] .```
  - run 
        ```$ docker run -p 5000:5000 [yourdockerimagename]```

####Before using it:
  - Make sure to insert your google and facebook credentials in secret_keys.py
  - Google credentials are included for the purposes of udacity grading
  - Facebook won’t redirect to localhost but you can see the running version on [FlutterHub]
  - Make sure to download the client_credentials.json from google and save it as such in the app directory
	Make sure to add the proper Database Connection string in other_info.py
	
####Requirements:
  - [python-flask]
  - [python-sqlalchemy]
  - [python-psycopg2] 
  - python2.7-dev
    
    
#####&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pip:

  - libjpeg-dev
  - zlib1g-dev
  - [pillow]
  - [oauth2client]
  - [dicttoxml]


### Json and XML endpoints:
  - `/json` or `/xml`
  
     Returns two objects - items and categories:
   
`{'items':[['item_title','item_category','item_url','item_id','item_picture','item_description','item_ownerName']],'categories':[]}`
  - `/[cateogry]/json` or `/[cateogry]/xml`
  
     Returns the items in the specified category and the other categories: 

  `{'items':[]}, 'categories':[]}`
  - `/[category]/[item_id]/json` or `/[category]/[item_id]/xml`
  
     Returns the owner of the post, the category and the item object:
  
`{'owner':{picture:'pictureurl', name:'Name', id:'userid'}, my_categry:"category", my_item:{itemobj}}`

### Version
0.0.1


License
----

MIT


**Free Software**
[FlutterHub]:http://www.flutterhub.com
[python-flask]:http://flask.pocoo.org/
[python-sqlalchemy]:http://www.sqlalchemy.org/
[python-psycopg2]:https://pypi.python.org/pypi/psycopg2
[pillow]:https://python-pillow.github.io/
[oauth2client]:https://github.com/google/oauth2client
[dicttoxml]:https://pypi.python.org/pypi/dicttoxml
[vagrant]:https://www.vagrantup.com/
[Docker]:https://www.docker.com/
[virtual-box]:https://www.virtualbox.org
