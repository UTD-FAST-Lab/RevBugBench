apt-get update && apt-get install -y git make autoconf automake libtool zlib1g-dev
git clone --no-checkout https://github.com/glennrp/libpng.git libpng
git -C libpng checkout -f a37d4836519517bdce6cb9d956092321eca3e73b
