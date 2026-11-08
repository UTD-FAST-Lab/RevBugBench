apt-get update && apt-get install -y git make autoconf automake libtool pkg-config zlib1g-dev liblzma-dev
git clone --no-checkout https://gitlab.gnome.org/GNOME/libxml2.git libxml2
git -C libxml2 checkout -f ec6e3efb06d7b15cf5a2328fabd3845acea4c815
