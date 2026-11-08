apt-get update && apt-get install -y make autoconf automake libtool pkg-config libbz2-dev liblzo2-dev liblzma-dev liblz4-dev libz-dev libxml2-dev libssl-dev libacl1-dev libattr1-dev
git clone https://github.com/libarchive/libarchive.git libarchive
git -C libarchive checkout -f 94ca3f0734f71a0d9389ceaa237ce5a4ed8a21cd
