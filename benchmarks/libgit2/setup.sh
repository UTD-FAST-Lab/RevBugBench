apt-get update && apt-get install -y make autoconf automake libtool cmake zip
git clone https://github.com/libgit2/libgit2 libgit2
git -C libgit2 checkout -f 20cb30b6b8e269d2ce3474523562b2739a8efea2
