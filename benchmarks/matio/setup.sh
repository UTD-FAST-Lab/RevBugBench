apt-get update && apt-get install -y make autoconf automake libhdf5-dev libtool zlib1g-dev wget zip
git clone https://github.com/tbeu/matio.git matio
git -C matio checkout -f aefd09e9d20aebb4a0b0a5e5c619f46038dba3bc
[ -f szip.tar.gz ] || wget -q -O szip.tar.gz https://support.hdfgroup.org/ftp/lib-external/szip/2.1.1/src/szip-2.1.1.tar.gz || wget -q -O szip.tar.gz https://ftp.osuosl.org/pub/blfs/conglomeration/szip/szip-2.1.1.tar.gz
