# mysite_nginx.conf

# the upstream component nginx needs to connect to
upstream django {
    server unix:///tmp/pydj.sock;
}

# configuration of the server
server {
    # the port your site will be served on
    listen      8000;
    # the domain name it will serve for
    server_name localhost; # substitute your machine's IP address or FQDN
    charset     utf-8;

    # max upload size
    client_max_body_size 75M;   # adjust to taste

    # Django media
    location /images  {
        alias /Users/Jon/pydj-test/playlist/images/;  # your Django project's media files - amend as required
    }

    location /static {
        alias /Users/Jon/pydj-test/static/; # your Django project's static files - amend as required
    }

    # Finally, send all non-media requests to the Django server.
    location / {
        uwsgi_pass  django;
        include     /Users/Jon/pydj-test/uwsgi_params; # the uwsgi_params file you installed
    }
}
