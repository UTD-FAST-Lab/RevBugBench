apt-get update && apt-get install -y git make autoconf automake libtool cmake nasm zlib1g-dev liblzma-dev libjpeg-turbo8-dev wget
git clone --no-checkout https://gitlab.com/libtiff/libtiff.git libtiff
git -C libtiff checkout -f c145a6c14978f73bb484c955eb9f84203efcb12e
