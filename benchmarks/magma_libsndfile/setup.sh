apt-get update && apt-get install -y git make autoconf autogen automake build-essential libasound2-dev libflac-dev libogg-dev libtool libvorbis-dev libopus-dev libmp3lame-dev libmpg123-dev pkg-config python
git clone --no-checkout https://github.com/libsndfile/libsndfile.git libsndfile
git -C libsndfile checkout -f 86c9f9eb7022d186ad4d0689487e7d4f04ce2b29
